# -*- coding: utf-8 -*-

import time
import re
import logging
import yaml
from aptly.exceptions import AptlyException, NoSuchPublish

lg = logging.getLogger(__name__)


def load_publish(publish):
    with open(publish, 'r') as publish_file:
        return yaml.load(publish_file)


class PublishManager(object):
    """
    Manage multiple publishes
    """
    def __init__(self, client):
        self.client = client
        self._publishes = {}
        self.timestamp = int(time.time())

    def publish(self, distribution):
        """
        Get or create publish
        """
        try:
            return self._publishes[distribution]
        except KeyError:
            self._publishes[distribution] = Publish(self.client, distribution, timestamp=self.timestamp)
            return self._publishes[distribution]

    def add(self, snapshot, distributions, component='main'):
        """ Add mirror or repo to publish """
        for dist in distributions:
            self.publish(dist).add(snapshot, component)

    def restore_publish(self, components, restore_file, recreate):
        publish_file = load_publish(restore_file)
        publish_source = Publish(self.client, publish_file.get('publish'))
        publish_source.restore_publish(publish_file,
                                       components=components,
                                       recreate=recreate)

    def dump_publishes(self, publishes_to_save, dump_dir, prefix):

        if len(dump_dir) > 1 and dump_dir[-1] == '/':
            dump_dir = dump_dir[:-1]

        save_list = []
        save_all = True

        if publishes_to_save and not ('all' in publishes_to_save):
            save_all = False

        publishes = self.client.do_get('/publish')
        for publish in publishes:
            name = '{}/{}'.format(publish['Prefix'], publish['Distribution'])
            if save_all or name in publishes_to_save:
                save_list.append(Publish(self.client, name, load=True))

        if not save_all and len(save_list) != len(publishes_to_save):
            raise Exception('Publish(es) required not found')

        for publish in save_list:
            save_path = ''.join([dump_dir, '/', prefix, publish.name.replace('/', '-')])
            publish.save_publish(save_path)

    def _publish_match(self, publish, names=False):
        """
        Check if publish name matches list of names or regex patterns
        """
        if names:
            for name in names:
                if isinstance(name, re._pattern_type):
                    if re.match(name, publish.name):
                        return True
                else:
                    if publish in [name, './%s' % name]:
                        return True
            return False
        else:
            return True

    def do_publish(self, *args, **kwargs):
        try:
            publish_names = kwargs.pop('names')
        except KeyError:
            publish_names = None

        for publish in self._publishes.values():
            if self._publish_match(publish.name, publish_names):
                publish.do_publish(*args, **kwargs)
            else:
                lg.info("Skipping publish %s not matching publish names" % publish.name)

    def list_uniq(self, seq):
        keys = {}
        for e in seq:
            keys[e] = 1
        return list(keys.keys())

    def cleanup_snapshots(self):
        snapshots = self.client.do_get('/snapshots', {'sort': 'time'})
        exclude = []

        # Add currently published snapshots into exclude list
        publishes = self.client.do_get('/publish')
        for publish in publishes:
            exclude.extend(
                [x['Name'] for x in publish['Sources']]
            )

        # Add last snapshots into exclude list
        # TODO: ignore snapshots that are source for merged snapshots
        snapshot_latest = []
        for snapshot in snapshots:
            base_name = snapshot['Name'].split('-')[0]
            if base_name not in snapshot_latest:
                snapshot_latest.append(base_name)
                if snapshot['Name'] not in exclude:
                    lg.debug("Not deleting latest snapshot %s" % snapshot['Name'])
                    exclude.append(snapshot['Name'])

        exclude = self.list_uniq(exclude)

        for snapshot in snapshots:
            if snapshot['Name'] not in exclude:
                lg.info("Deleting snapshot %s" % snapshot['Name'])
                try:
                    self.client.do_delete('/snapshots/%s' % snapshot['Name'])
                except AptlyException as e:
                    if e.res.status_code == 409:
                        lg.warning("Snapshot %s is being used, can't delete" % snapshot['Name'])
                    else:
                        raise


class Publish(object):
    """
    Single publish object
    """
    def __init__(self, client, distribution, timestamp=None, recreate=False, load=False, merge_prefix='_'):
        self.client = client
        self.recreate = recreate

        dist_split = distribution.split('/')
        self.distribution = dist_split[-1]
        if dist_split[0] != self.distribution:
            self.prefix = dist_split[0]
        else:
            self.prefix = ''

        self.name = '%s/%s' % (self.prefix or '.', self.distribution)

        if not timestamp:
            self.timestamp = int(time.time())
        else:
            self.timestamp = timestamp

        self.merge_prefix = merge_prefix
        self.components = {}
        self.publish_snapshots = []

        if load:
            # Load information from remote immediately
            self.load()

    def __eq__(self, other):
        if not isinstance(other, Publish):
            return False

        diff, equal = self.compare(other)
        if not diff:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def compare(self, other, components=[]):
        """
        Compare two publishes
        It expects that other publish is same or older than this one

        Return tuple (diff, equal) of dict {'component': ['snapshot']}
        """
        lg.debug("Comparing publish %s and %s" % (self.name, other.name))

        diff, equal = ({}, {})

        for component, snapshots in self.components.items():
            if component not in list(other.components.keys()):
                # Component is missing in other
                diff[component] = snapshots
                continue

            equal_snapshots = list(set(snapshots).intersection(other.components[component]))
            if equal_snapshots:
                lg.debug("Equal snapshots for %s: %s" % (component, equal_snapshots))
                equal[component] = equal_snapshots

            diff_snapshots = list(set(snapshots).difference(other.components[component]))
            if diff_snapshots:
                lg.debug("Different snapshots for %s: %s" % (component, diff_snapshots))
                diff[component] = diff_snapshots

        return (diff, equal)

    def _get_publish(self):
        """
        Find this publish on remote
        """
        publishes = self.client.do_get('/publish')
        for publish in publishes:
            if publish['Distribution'] == self.distribution and \
                    publish['Prefix'] == (self.prefix or '.'):
                return publish
        raise NoSuchPublish("Publish %s does not exist" % self.name)

    def _remove_snapshots(self, snapshots):
        for snapshot in snapshots:
            self.client.do_delete('/snapshots/%s' % snapshot)

    def save_publish(self, save_path):
        """
        Serialize publish in YAML
        """
        name = self.name.replace('/', '-')
        timestamp = time.strftime("%Y%m%d%H%M%S")

        yaml_dict = {}
        yaml_dict["publish"] = self.name
        yaml_dict["name"] = timestamp
        yaml_dict["components"] = []
        for component, snapshots in self.components.items():
            packages = self.get_packages(component)
            package_dict = []
            for package in packages:
                (arch, name, version, ref) = self.parse_package_ref(package)
                package_dict.append({'package': name, 'version': version, 'arch': arch, 'ref': ref})
            snapshot = self._find_snapshot(snapshots[0])

            yaml_dict["components"].append({'component': component, 'snapshot': snapshot['Name'],
                                            'description': snapshot['Description'], 'packages': package_dict})

        lg.info("Saving publish %s in %s" % (name, save_path))
        with open(save_path, 'w') as save_file:
            yaml.dump(yaml_dict, save_file, default_flow_style=False)

    def restore_publish(self, config, components, recreate=False):
        """
        Restore publish from config file
        """
        if "all" in components:
            components = []

        try:
            self.load()
            publish = True
        except NoSuchPublish:
            publish = False

        new_publish_snapshots = []
        to_publish = []
        created_snapshots = []

        for saved_component in config.get('components', []):
            component_name = saved_component.get('component')

            if not component_name:
                raise Exception("Corrupted file")

            if components and component_name not in components:
                continue

            saved_packages = []
            if not saved_component.get('packages'):
                raise Exception("Component %s is empty" % component_name)

            for package in saved_component.get('packages'):
                package_ref = '{} {} {} {}'.format(package.get('arch'), package.get('package'), package.get('version'), package.get('ref'))
                saved_packages.append(package_ref)

            to_publish.append(component_name)

            snapshot_name = '{}-{}'.format("restored", saved_component.get('snapshot'))
            lg.debug("Creating snapshot %s for component %s of packages: %s"
                     % (snapshot_name, component_name, saved_packages))

            try:
                self.client.do_post(
                    '/snapshots',
                    data={
                        'Name': snapshot_name,
                        'SourceSnapshots': [],
                        'Description': saved_component.get('description'),
                        'PackageRefs': saved_packages,
                    }
                )
                created_snapshots.append(snapshot_name)
            except AptlyException as e:
                if e.res.status_code == 404:
                    # delete all the previously created
                    # snapshots because the file is corrupted
                    self._remove_snapshots(created_snapshots)
                    raise Exception("Source snapshot or packages don't exist")

            new_publish_snapshots.append({
                'Component': component_name,
                'Name': snapshot_name
            })

        if components:
            self.publish_snapshots = [x for x in self.publish_snapshots if x['Component'] not in components and x['Component'] not in to_publish]
            check_components = [x for x in new_publish_snapshots if x['Component'] in components]
            if len(check_components) != len(components):
                self._remove_snapshots(created_snapshots)
                raise Exception("Not possible to find all the components required in the backup file")

        self.publish_snapshots += new_publish_snapshots
        self.do_publish(recreate=recreate, merge_snapshots=False)

    def load(self):
        """
        Load publish info from remote
        """
        publish = self._get_publish()
        for source in publish['Sources']:
            component = source['Component']
            snapshot = source['Name']
            self.publish_snapshots.append({
                'Component': component,
                'Name': snapshot
            })

            snapshot_remote = self._find_snapshot(snapshot)
            for source in self._get_source_snapshots(snapshot_remote, fallback_self=True):
                self.add(source, component)

    def get_packages(self, component=None, components=[], packages=None):
        """
        Return package refs for given components
        """
        if component:
            components = [component]

        package_refs = []
        for snapshot in self.publish_snapshots:
            if component and snapshot['Component'] not in components:
                # We don't want packages for this component
                continue

            component_refs = self.client.do_get('/snapshots/%s/packages' % snapshot['Name'])
            if packages:
                # Filter package names
                for ref in component_refs:
                    if self.parse_package_ref(ref)[1] in packages:
                        package_refs.append(ref)
            else:
                package_refs.extend(component_refs)

        return package_refs

    def parse_package_ref(self, ref):
        """
        Return tuple of architecture, package_name, version, id
        """
        if not ref:
            return None
        parsed = re.match('(.*)\ (.*)\ (.*)\ (.*)', ref)
        return parsed.groups()

    def add(self, snapshot, component='main'):
        """
        Add snapshot of component to publish
        """
        try:
            self.components[component].append(snapshot)
        except KeyError:
            self.components[component] = [snapshot]

    def _find_snapshot(self, name):
        """
        Find snapshot on remote by name or regular expression
        """
        remote_snapshots = self.client.do_get('/snapshots', {'sort': 'time'})
        for remote in reversed(remote_snapshots):
            if remote["Name"] == name or \
                    re.match(name, remote["Name"]):
                return remote
        return None

    def _get_source_snapshots(self, snapshot, fallback_self=False):
        """
        Get list of source snapshot names of given snapshot

        TODO: we have to decide by description at the moment
        """
        if not snapshot:
            return []

        source_snapshots = re.findall(r"'([\w\d\.-]+)'", snapshot['Description'])
        if not source_snapshots and fallback_self:
            source_snapshots = [snapshot['Name']]

        source_snapshots.sort()
        return source_snapshots

    def merge_snapshots(self):
        """
        Create component snapshots by merging other snapshots of same component
        """
        self.publish_snapshots = []
        for component, snapshots in self.components.items():
            if len(snapshots) <= 1:
                # Only one snapshot, no need to merge
                lg.debug("Component %s has only one snapshot %s, not creating merge snapshot" % (component, snapshots))
                self.publish_snapshots.append({
                    'Component': component,
                    'Name': snapshots[0]
                })
                continue

            # Look if merged snapshot doesn't already exist
            remote_snapshot = self._find_snapshot(r'^%s%s-%s-\d+' % (self.merge_prefix, self.name.replace('./', '').replace('/', '-'), component))
            if remote_snapshot:
                source_snapshots = self._get_source_snapshots(remote_snapshot)

                # Check if latest merged snapshot has same source snapshots like us
                snapshots_want = list(snapshots)
                snapshots_want.sort()

                lg.debug("Comparing snapshots: snapshot_name=%s, snapshot_sources=%s, wanted_sources=%s" % (remote_snapshot['Name'], source_snapshots, snapshots_want))
                if snapshots_want == source_snapshots:
                    lg.info("Remote merge snapshot already exists: %s (%s)" % (remote_snapshot['Name'], source_snapshots))
                    self.publish_snapshots.append({
                        'Component': component,
                        'Name': remote_snapshot['Name']
                    })
                    continue

            snapshot_name = '%s%s-%s-%s' % (self.merge_prefix, self.name.replace('./', '').replace('/', '-'), component, self.timestamp)
            lg.info("Creating merge snapshot %s for component %s of snapshots %s" % (snapshot_name, component, snapshots))
            package_refs = []
            for snapshot in snapshots:
                # Get package refs from each snapshot
                packages = self.client.do_get('/snapshots/%s/packages' % snapshot)
                package_refs.extend(packages)

            self.client.do_post(
                '/snapshots',
                data={
                    'Name': snapshot_name,
                    'SourceSnapshots': snapshots,
                    'Description': "Merged from sources: %s" % ', '.join("'%s'" % snap for snap in snapshots),
                    'PackageRefs': package_refs,
                }
            )

            self.publish_snapshots.append({
                'Component': component,
                'Name': snapshot_name
            })

    def drop_publish(self):
        lg.info("Deleting publish, distribution=%s" % self.name)

        self.client.do_delete('/publish/%s/%s' % (self.prefix, self.distribution))

    def update_publish(self, force_overwrite=False, publish_contents=False):
        lg.info("Updating publish, distribution=%s snapshots=%s" %
                (self.name, self.publish_snapshots))

        self.client.do_put(
            '/publish/%s/%s' % (self.prefix, self.distribution),
            {
                'Snapshots': self.publish_snapshots,
                'ForceOverwrite': force_overwrite,
                'SkipContents': not publish_contents,
            }
        )

    def create_publish(self, force_overwrite=False, publish_contents=False, architectures=None):
        lg.info("Creating new publish, distribution=%s snapshots=%s, architectures=%s" %
                (self.name, self.publish_snapshots, architectures))

        if self.prefix:
            prefix = '/%s' % self.prefix

        opts = {
            "SourceKind": "snapshot",
            "Distribution": self.distribution,
            "Sources": self.publish_snapshots,
            "ForceOverwrite": force_overwrite,
            'SkipContents': not publish_contents,
        }

        if architectures:
            opts['Architectures'] = architectures

        self.client.do_post(
            '/publish%s' % (prefix or ''),
            opts
        )

    def do_publish(self, recreate=False, no_recreate=False,
                   force_overwrite=False, publish_contents=False,
                   architectures=None, merge_snapshots=True):
        if merge_snapshots:
            self.merge_snapshots()
        try:
            publish = self._get_publish()
        except NoSuchPublish:
            publish = False

        if not publish:
            # New publish
            self.create_publish(force_overwrite, publish_contents, architectures)
        else:
            # Test if publish is up to date
            to_publish = [x['Name'] for x in self.publish_snapshots]
            published = [x['Name'] for x in publish['Sources']]

            to_publish.sort()
            published.sort()

            if recreate:
                lg.info("Recreating publish %s" % self.name)
                self.drop_publish()
                self.create_publish(force_overwrite, publish_contents, architectures)
            elif to_publish == published:
                lg.info("Publish %s is up to date" % self.name)
            else:
                try:
                    self.update_publish(force_overwrite, publish_contents)
                except AptlyException as e:
                    if e.res.status_code == 404:
                        # Publish exists but we are going to add some new
                        # components. Unfortunately only way is to recreate it
                        if no_recreate:
                            lg.error("Cannot update publish %s (adding new components?), falling back to recreating it is disabled so skipping.")
                        else:
                            lg.warning("Cannot update publish %s (adding new components?), falling back to recreating it" % self.name)
                            self.drop_publish()
                            self.create_publish(force_overwrite, publish_contents, architectures)
