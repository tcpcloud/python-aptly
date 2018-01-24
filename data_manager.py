#!/usr/bin/env python3

from aptly.client import Aptly
from aptly.publisher import Publish

import time
import datetime

class DataManager:
    def __init__(self):
        self.publish_dict = {}
        self.client = None

    def create_client(self, url, timeout=600):
        self.client = Aptly(url, dry=False, timeout=timeout)

    def get_client(self):
        return self.client

    def get_publish_dict(self):
        return self.publishDict

    def get_publish_list(self):
        return sorted(self.publish_dict.keys())

    def get_publish(self, name):
        self.publish_dict[name].load()
        return self.publish_dict[name]

    def get_package_from_publish_component(self, publish, component):
        snapshot = self.publish_dict[publish].components[component][0]

        return sorted(Publish._get_packages(self.client, "snapshots", snapshot))

    @staticmethod
    def generate_snapshot_name(old_snapshot):
        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
        return "{}-{}-{}".format(old_snapshot, "merged-gui", st)

