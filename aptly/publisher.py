#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from aptly.client import Aptly, Publish
import yaml
import logging

logging.basicConfig()
lg_root = logging.getLogger('aptly')


def load_config(config):
    with open(config, 'r') as fh:
        return yaml.load(fh)


def get_latest_snapshot(snapshots, name):
    for snapshot in snapshots:
        if snapshot['Name'].startswith('%s-' % name):
            return snapshot['Name']


def main():
    parser = argparse.ArgumentParser("Aptly publisher")
    parser.add_argument('-c', '--config', default="/etc/aptly/publisher.yaml", help="Configuration YAML file")
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-d', '--debug', action="store_true")
    parser.add_argument('--dry', '--dry-run', action="store_true")
    parser.add_argument('url', help="URL to Aptly API, eg. http://localhost:8080")
    args = parser.parse_args()

    if args.verbose:
        lg_root.setLevel(logging.INFO)

    if args.debug:
        lg_root.setLevel(logging.DEBUG)

    config = load_config(args.config)

    client = Aptly(args.url, dry=args.dry)
    publish = Publish(client)

    snapshots = client.do_get('/snapshots', {'sort': 'time'})

    for name, repo in config.get('mirror', {}).iteritems():
        publish.add(
            name,
            component=repo.get('component', 'main'),
            distributions=repo['distributions'],
            snapshot=get_latest_snapshot(snapshots, name)
        )

    for name, repo in config.get('repo', {}).iteritems():
        publish.add(
            name,
            component=repo.get('component', 'main'),
            distributions=repo['distributions'],
            snapshot=get_latest_snapshot(snapshots, name)
        )

    publish.merge_snapshots()
    publish.do_publish()


if __name__ == '__main__':
    main()
