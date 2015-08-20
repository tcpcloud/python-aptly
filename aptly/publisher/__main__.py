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
lg = logging.getLogger(__name__)


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
        action_promote(client, source=args.source, target=args.target, components=args.components, recreate=args.recreate)
    elif args.action == 'cleanup':
        publishmgr.cleanup_snapshots()
        sys.exit(0)


def action_promote(client, source, target, components=None, recreate=False):
    try:
        publish_source = Publish(client, source, load=True)
    except NoSuchPublish as e:
        lg.error(e)
        sys.exit(1)

    publish_target = Publish(client, target)
    try:
        publish_target.load()
    except NoSuchPublish:
        # Target doesn't have to exist, it will be created
        pass

    if not components:
        publish_target.components = copy.deepcopy(publish_source.components)
    else:
        for component in components:
            try:
                publish_target.components[component] = copy.deepcopy(publish_source.component[component])
            except KeyError:
                lg.error("Component %s does not exist")
                sys.exit(1)
    publish_target.do_publish(recreate=recreate)


def action_publish(client, publishmgr, config_file, recreate=False):
    snapshots = client.do_get('/snapshots', {'sort': 'time'})

    config = load_config(config_file)
    for name, repo in config.get('mirror', {}).iteritems():
        snapshot = get_latest_snapshot(snapshots, name)
        if not snapshot:
            continue
        publishmgr.add(
            name,
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
