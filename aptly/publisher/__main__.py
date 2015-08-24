#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
lg_root = logging.getLogger('aptly')
lg = logging.getLogger('aptly-publisher')


def load_config(config):
    with open(config, 'r') as fh:
        return yaml.load(fh)


def get_latest_snapshot(snapshots, name):
    for snapshot in reversed(snapshots):
        if re.match(r'%s-\d+' % name, snapshot['Name']):
            return snapshot['Name']


def main():
    parser = argparse.ArgumentParser("Aptly publisher")

    group_common = parser.add_argument_group("Common")
    parser.add_argument('action', help="Action to perform (publish, promote, cleanup)")
    group_common.add_argument('-v', '--verbose', action="store_true")
    group_common.add_argument('-d', '--debug', action="store_true")
    group_common.add_argument('--dry', '--dry-run', action="store_true")
    group_common.add_argument('--url', required=True, help="URL to Aptly API, eg. http://localhost:8080")
    group_common.add_argument('--recreate', action="store_true", help="Drop publish and create it again, only way to add new components")

    group_publish = parser.add_argument_group("Action 'publish'")
    group_publish.add_argument('-c', '--config', default="/etc/aptly/publisher.yaml", help="Configuration YAML file")

    group_promote = parser.add_argument_group("Action 'promote'")
    group_promote.add_argument('--source', help="Source publish to take snapshots from")
    group_promote.add_argument('--target', help="Target publish to update")
    group_promote.add_argument('--components', nargs='+', help="Space-separated list of components to promote")
    group_promote.add_argument('--diff', action="store_true", help="Show differences between publishes (snapshots to be updated)")

    args = parser.parse_args()

    if args.verbose:
        lg_root.setLevel(logging.INFO)

    if args.debug:
        lg_root.setLevel(logging.DEBUG)

    client = Aptly(args.url, dry=args.dry)
    publishmgr = PublishManager(client)

    if args.action == 'publish':
        action_publish(client, publishmgr, config_file=args.config, recreate=args.recreate)
    elif args.action == 'promote':
        if not args.source or not args.target:
            parser.error("Action 'promote' requires both --source and --target arguments")
        action_promote(client, source=args.source, target=args.target,
                       components=args.components, recreate=args.recreate,
                       diff=args.diff)
    elif args.action == 'cleanup':
        publishmgr.cleanup_snapshots()
        sys.exit(0)


def action_promote(client, source, target, components=None, recreate=False,
                   diff=False):
    try:
        publish_source = Publish(client, source, load=True)
    except NoSuchPublish as e:
        lg.error(e)
        sys.exit(1)

    publish_target = Publish(client, target)
    try:
        publish_target.load()
    except NoSuchPublish:
        if diff:
            lg.error("Target publish %s does not exist" % target)
            sys.exit(1)
        # Target doesn't have to exist, it will be created
        pass

    if diff:
        action_diff(source=publish_source, target=publish_target, components=components)
    else:
        if not components:
            publish_target.components = copy.deepcopy(publish_source.components)
        else:
            for component in components:
                try:
                    publish_target.components[component] = copy.deepcopy(publish_source.components[component])
                except KeyError:
                    lg.error("Component %s does not exist")
                    sys.exit(1)

        if publish_source == publish_target:
            lg.warn("Target is up to date with source publish")
            if not recreate:
                lg.warn("There is nothing to do")
                sys.exit(0)
            else:
                lg.warn("Recreating publish on your command")
        publish_target.do_publish(recreate=recreate)


def action_diff(source, target, components=[], packages=True):
    diff, equal = source.compare(target, components=components)
    if not diff:
        print "Target is up to date with source publish"
        return

    print "\033[1;36m= Differencies per component\033[m"
    for component, snapshots in diff.iteritems():
        if not snapshots:
            continue

        published_source = [i for i in source.publish_snapshots if i['Component'] == component][0]['Name']
        published_target = [i for i in target.publish_snapshots if i['Component'] == component][0]['Name']

        print "\033[1;33m== %s \033[1;30m(%s -> %s)\033[m" % (component, published_target, published_source)
        print "\033[1;35m=== Snapshots:\033[m"
        for snapshot in snapshots:
            print "    - %s" % snapshot

        if packages:
            print "\033[1;35m=== Packages:\033[m"
            diff_packages = source.client.do_get('/snapshots/%s/diff/%s' % (published_source, published_target))
            if not diff_packages:
                print "\033[1;31m    - Snapshots contain same packages\033[m"

            for pkg in diff_packages:
                if not pkg['Left']:
                    # Parse pkg name from target if not in source
                    # This should not happen and is mostly caused by this bug:
                    # https://github.com/smira/aptly/issues/287
                    pkg_name = re.match('.*\ (.*)\ .*\ .*', pkg['Right']).group(1)
                else:
                    pkg_name = re.match('.*\ (.*)\ .*\ .*', pkg['Left']).group(1)

                if pkg['Left']:
                    new = re.match('.*\ .*\ (.*)\ .*', pkg['Left']).group(1)
                else:
                    new = pkg['Left']

                if pkg['Right']:
                    old = re.match('.*\ .*\ (.*)\ .*', pkg['Right']).group(1)
                else:
                    old = pkg['Right']

                print '    - %s \033[1;30m(%s -> %s)\033[m' % (pkg_name, old, new)

        print


def action_publish(client, publishmgr, config_file, recreate=False):
    snapshots = client.do_get('/snapshots', {'sort': 'time'})

    config = load_config(config_file)
    for name, repo in config.get('mirror', {}).iteritems():
        snapshot = get_latest_snapshot(snapshots, name)
        if not snapshot:
            continue
        publishmgr.add(
            component=repo.get('component', 'main'),
            distributions=repo['distributions'],
            snapshot=snapshot
        )

    for name, repo in config.get('repo', {}).iteritems():
        snapshot = get_latest_snapshot(snapshots, name)
        if not snapshot:
            continue
        publishmgr.add(
            component=repo.get('component', 'main'),
            distributions=repo['distributions'],
            snapshot=snapshot
        )

    publishmgr.do_publish(recreate=recreate)


if __name__ == '__main__':
    main()
