#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import argparse
from aptly.client import Aptly
from aptly.publisher import PublishManager, Publish
from aptly.exceptions import NoSuchPublish
import yaml
import logging
import copy
import re

logging.basicConfig()
lg_aptly = logging.getLogger('aptly')
lg = logging.getLogger('aptly-publisher')


def load_config(config):
    with open(config, 'r') as fh:
        return yaml.load(fh)


def get_latest_snapshot(snapshots, name):
    for snapshot in reversed(snapshots):
        if re.match(r'%s-\d+' % name, snapshot['Name']):
            return snapshot['Name']


def main():
    parser = argparse.ArgumentParser("aptly-publisher")

    group_common = parser.add_argument_group("Common")
    parser.add_argument('action', help="Action to perform (publish, promote, cleanup, restore, dump, purge)")
    group_common.add_argument('-v', '--verbose', action="store_true")
    group_common.add_argument('-d', '--debug', action="store_true")
    group_common.add_argument('--dry', '--dry-run', action="store_true")
    group_common.add_argument('--timeout', type=int, default=300, help="Aptly client timeout. Raise for larger publishes and slow server.")
    group_common.add_argument('--url', required=True, help="URL to Aptly API, eg. http://localhost:8080")
    group_common.add_argument('--recreate', action="store_true", help="Drop publish and create it again, only way to add new components")
    group_common.add_argument('--no-recreate', action="store_true", help="Never recreate publish (even when we are adding new components where it's the only option)")
    group_common.add_argument('--force-overwrite', action="store_true", help="Overwrite files in pool/ directory without notice")
    group_common.add_argument('--publish-contents', action="store_true", default=False, help="Publish contents. It's slow so disabled by default to support large repositories.")
    group_common.add_argument('--components', nargs='+', help="Space-separated list of components to promote or restore or to purge (in case of purge)")
    group_common.add_argument('--storage', default="", help="Storage backend to use for all publishes, can be empty (filesystem, default), swift:[name] or s3:[name]")
    group_common.add_argument('-p', '--publish', nargs='+', help="Space-separated list of publish")

    group_publish = parser.add_argument_group("Action 'publish'")
    group_publish.add_argument('-c', '--config', default="/etc/aptly/publisher.yaml", help="Configuration YAML file")
    group_publish.add_argument('--dists', nargs='+', help="Space-separated list of distribution to work with (including prefix), default all.")
    group_publish.add_argument('--architectures', nargs='+', help="List of architectures to publish (also determined by config, defaults to amd64, i386)")
    group_publish.add_argument('--only-latest', action="store_true", default=False, help="Publish only latest packages of every publishes")

    group_promote = parser.add_argument_group("Action 'promote'")
    group_promote.add_argument('--source', help="Source publish to take snapshots from. Can be regular expression, eg. jessie(/?.*)/nightly")
    group_promote.add_argument('--target', help="Target publish to update. Must be format if source is regex, eg. jessie{0}/testing")
    group_promote.add_argument('--packages', nargs='+', help="Space-separated list of packages to promote")
    group_promote.add_argument('--diff', action="store_true", help="Show differences between publishes (snapshots to be updated)")

    group_purge = parser.add_argument_group("Purge")
    group_purge.add_argument('--hard', action="store_true", default=False, help="Remove all unused packages and snapshots")

    group_restore = parser.add_argument_group("Action 'restore'")
    group_restore.add_argument('-r', '--restore-file', help="File used to restore publish")

    group_save = parser.add_argument_group("Action 'dump'")
    group_save.add_argument('-s', '--save-dir', default='.', help="Path of where dump of publish will be done")
    group_save.add_argument('-x', '--prefix', default="saved-", help="Prefix for dump files' names")

    args = parser.parse_args()

    if args.verbose:
        lg_aptly.setLevel(logging.INFO)
        lg.setLevel(logging.INFO)

    if args.debug:
        lg_aptly.setLevel(logging.DEBUG)
        lg.setLevel(logging.DEBUG)

    client = Aptly(args.url, dry=args.dry, timeout=args.timeout)
    publishmgr = PublishManager(client, storage=args.storage)

    if args.action == 'publish':
        action_publish(client, publishmgr, config_file=args.config,
                       recreate=args.recreate,
                       no_recreate=args.no_recreate,
                       force_overwrite=args.force_overwrite,
                       publish_contents=args.publish_contents,
                       publish_names=args.publish,
                       publish_dist=args.dists,
                       architectures=args.architectures,
                       only_latest=args.only_latest,
                       components=args.components)
    elif args.action == 'promote':
        if not args.source or not args.target:
            parser.error("Action 'promote' requires both --source and --target arguments")
        action_promote(client, source=args.source, target=args.target,
                       components=args.components, recreate=args.recreate,
                       no_recreate=args.no_recreate, packages=args.packages,
                       diff=args.diff, force_overwrite=args.force_overwrite,
                       publish_contents=args.publish_contents,
                       storage=args.storage)
    elif args.action == 'cleanup':
        publishmgr.cleanup_snapshots()
        sys.exit(0)
    elif args.action == 'dump':
        action_dump(publishmgr, args.save_dir, args.publish, args.prefix)
    elif args.action == 'purge':
        config = load_config(args.config)
        publishmgr.do_purge(config, components=args.components, hard_purge=args.hard)
    elif args.action == "restore":
        action_restore(publishmgr, components=args.components,
                       recreate=args.recreate,
                       restore_file=args.restore_file)

def promote(client, source, target, components=None, recreate=False,
            no_recreate=False, packages=None, diff=False, force_overwrite=False,
            publish_contents=False, storage=""):
    try:
        publish_source = Publish(client, source, load=True, storage=storage)
    except NoSuchPublish as e:
        lg.error(e)
        sys.exit(1)

    publish_target = Publish(client, target, storage=storage)
    try:
        publish_target.load()
    except NoSuchPublish:
        if diff:
            lg.error("Target publish %s does not exist" % target)
            sys.exit(1)
        # Target doesn't have to exist, it will be created
        pass

    if diff:
        # Only print differences and exit
        action_diff(source=publish_source, target=publish_target, components=components)
        sys.exit(0)

    # Check if target is not already up to date
    diffs, equals = publish_source.compare(publish_target, components=components)
    if not diffs:
        lg.warn("Target {0} is up to date with source publish {1}".format(target, source))
        if not recreate:
            lg.warn("There is nothing to do with target publish {0}".format(target))
            sys.exit(0)
        else:
            lg.warn("Recreating target publish {0} on your command".format(target))

    if packages:
        # We are only going to promote specific packages
        packages_promoted = False
        for component, snapshots in publish_source.components.items():
            if components and component not in components:
                # We don't want to promote this component
                continue

            # Get packages to promote
            package_refs = publish_source.get_packages(component=component, packages=packages)
            if package_refs:
                # Create snapshot for selected packages
                snapshot_name = 'ext_%s-%s' % (component, publish_target.timestamp)
                lg.debug("Creating snapshot %s for component %s of packages: %s" % (snapshot_name, component, packages))
                client.do_post(
                    '/snapshots',
                    data={
                        'Name': snapshot_name,
                        'SourceSnapshots': snapshots,
                        'Description': "Promoted packages from snapshots %s: %s" % (snapshots, packages),
                        'PackageRefs': package_refs,
                    }
                )
                publish_target.components[component].append(snapshot_name)
                packages_promoted = True
        if not packages_promoted:
            lg.error("No packages were promoted : are you sure components: %s and packages: %s are valid?" % (components, packages))
            sys.exit(1)
    else:
        # Publish whole components
        # Use source publish components structure for creation of target publish
        if not components:
            publish_target.components = copy.deepcopy(publish_source.components)
        else:
            for component in components:
                try:
                    publish_target.components[component] = copy.deepcopy(publish_source.components[component])
                except KeyError:
                    lg.error("Component %s does not exist")
                    sys.exit(1)

    publish_target.do_publish(recreate=recreate, no_recreate=no_recreate,
                              force_overwrite=force_overwrite,
                              publish_contents=publish_contents)

def find_publishes(client, source, target):
    ret = []
    if not re.search(r'{[0-9]+}', target):
        lg.error("Source publish is regular expression but target does not refer any match groups. See help for more info.")
        sys.exit(1)
    lg.debug("Looking for source publishes matching regular expression: {0}".format(source))
    publishes = client.do_get('/publish')
    re_source = re.compile(source)
    for publish in publishes:
        name = "{}{}{}".format(publish['Storage']+":" if publish['Storage']
                                else "", publish['Prefix']+"/" if
                                publish['Prefix'] else "",
                                publish['Distribution'])
        match = re_source.match(name)
        if match:
            try:
                target_parsed = target.format(*match.groups())
            except IndexError:
                lg.error("Can't format target publish {0} using groups {1}".format(target_parsed, match.groups()))
                sys.exit(1)
            ret.append((name, target_parsed))
    return ret


def action_promote(client, **kwargs):
    # Determine if source is regular expression with group, in this case, we
    # will work with multiple publishes
    if re.search(r'\(.*\)', kwargs['source']):
        for publish in find_publishes(client, kwargs['source'], kwargs['target']):
            source = publish[0]
            target = publish[1]
            lg.info("Found source publish matching regex, promoting {0} to {1}".format(source, target))
            kwargs_copy = kwargs.copy()
            kwargs_copy['source'] = source
            kwargs_copy['target'] = target
            try:
                promote(client, **kwargs_copy)
            except SystemExit:
                pass
    else:
        promote(client, **kwargs)

def action_dump(publishmgr, path, publish_to_save, prefix):
    publishmgr.dump_publishes(publish_to_save, path, prefix)


def action_restore(publishmgr, components, restore_file, recreate):
    publishmgr.restore_publish(components, restore_file, recreate)


def action_diff(source, target, components=[], packages=True):
    diff, equal = source.compare(target, components=components)
    if not diff:
        print("Target {0} is up to date with source publish {1}".format(target.full_name.replace('_', '/'), source.full_name.replace('_', '/')))
        return

    print("\033[1;36m= Differencies per component\033[m")
    for component, snapshots in diff.items():
        if not snapshots:
            continue

        published_source = [i for i in source.publish_snapshots if i['Component'] == component][0]['Name']
        published_target = [i for i in target.publish_snapshots if i['Component'] == component][0]['Name']

        print("\033[1;33m== %s \033[1;30m(%s -> %s)\033[m" % (component, published_target, published_source))
        print("\033[1;35m=== Snapshots:\033[m")
        for snapshot in snapshots:
            print("    - %s" % snapshot)

        if packages:
            print("\033[1;35m=== Packages:\033[m")
            diff_packages = source.client.do_get('/snapshots/%s/diff/%s' % (published_source, published_target))
            if not diff_packages:
                print("\033[1;31m    - Snapshots contain same packages\033[m")

            for pkg in diff_packages:
                left = source.parse_package_ref(pkg['Left'])
                right = target.parse_package_ref(pkg['Right'])

                if not left:
                    # Parse pkg name from target if not in source
                    # This should not happen and is mostly caused by this bug:
                    # https://github.com/smira/aptly/issues/287
                    pkg_name = right[1]
                else:
                    pkg_name = left[1]

                if left:
                    new = left[2]
                else:
                    new = pkg['Left']

                if right:
                    old = right[2]
                else:
                    old = pkg['Right']

                print('    - %s \033[1;30m(%s -> %s)\033[m' % (pkg_name, old, new))

        print()


def action_publish(client, publishmgr, config_file, recreate=False,
                   no_recreate=False, force_overwrite=False,
                   publish_contents=False, publish_dist=None, publish_names=None,
                   architectures=None, only_latest=False, components=[]):
    if not architectures:
        architectures = []
    snapshots = client.do_get('/snapshots', {'sort': 'time'})

    config = load_config(config_file)
    for name, repo in config.get('mirror', {}).items():
        snapshot = get_latest_snapshot(snapshots, name)
        if not snapshot:
            continue
        publishmgr.add(
            component=repo.get('component', 'main'),
            distributions=repo['distributions'],
            storage=repo.get('storage', ""),
            snapshot=snapshot
        )
        for arch in repo.get('architectures', []):
            if arch not in architectures:
                architectures.append(arch)

    for name, repo in config.get('repo', {}).items():
        snapshot = get_latest_snapshot(snapshots, name)
        if not snapshot:
            continue
        publishmgr.add(
            component=repo.get('component', 'main'),
            distributions=repo['distributions'],
            storage=repo.get('storage', ""),
            snapshot=snapshot
        )
        for arch in repo.get('architectures', []):
            if arch not in architectures:
                architectures.append(arch)

    publishmgr.do_publish(recreate=recreate, no_recreate=no_recreate,
                          force_overwrite=force_overwrite,
                          publish_contents=publish_contents, dist=publish_dist,
                          names=publish_names, architectures=architectures,
                          only_latest=only_latest, config=config,
                          components=components)


if __name__ == '__main__':
    main()
