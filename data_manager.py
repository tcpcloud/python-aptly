#!/usr/bin/env python3

from aptly.client import Aptly
from aptly.publisher import Publish

class DataManager:
    def __init__(self):
        self.publish_dict = {}
        self.client = None

    def create_client(self, url, timeout=600):
        self.client = Aptly(url, dry=False, timeout=timeout)

    def preLoadPublishes(self):
        publishes = self.client.do_get('/publish')
        for publish in publishes:
            name = "{}{}{}".format(publish['Storage'] + ":" if publish['Storage']
                                   else "", publish['Prefix'] + "/" if
                                   publish['Prefix'] else "",
                                   publish['Distribution'])
            self.publishDict[name] = Publish(self.client, name, load=False, storage=publish.get('Storage', "local"))

    def get_client(self):
        return self.client

    def get_publish_dict(self):
        return self.publishDict