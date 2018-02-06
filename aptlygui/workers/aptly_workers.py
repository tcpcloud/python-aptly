#!/usr/bin/env python3

from PyQt5.QtCore import QThread
from aptly.publisher import Publish
from PyQt5.QtCore import pyqtSignal


class DataThread(QThread):
    log = pyqtSignal(str, str)
    progress = pyqtSignal(int)

    def __init__(self, dataManager):
        super(DataThread, self).__init__()
        self.client = dataManager.client
        self.data_manager = dataManager
        self.cancelled = False

    def run(self):
        publish_dict = {}
        repo_dict = {}

        try:
            publishes = self.client.do_get('/publish')
            repos = self.client.do_get('/repos')
        except Exception as e:
            self.log.emit(e, "error")
            self.terminate()

        i = 0
        nb_max = len(publishes) + len(repos)

        for repo in repos:
            i += 1
            self.log.emit("Loading repository {0}".format(repo["Name"]), "info")
            self.progress.emit(i / nb_max * 100)
            repo_dict[repo["Name"]] = sorted(Publish._get_packages(self.data_manager.get_client(), "repos", repo["Name"]))

        for publish in publishes:
            i += 1
            name = "{}{}{}".format(publish['Storage'] + ":"
                                   if publish['Storage']
                                   else "", publish['Prefix'] + "/" if
                                   publish['Prefix'] else "",
                                   publish['Distribution'])

            # Only publishes made of snapshots are loaded, others are managed in the repository tab
            if publish['SourceKind'] != 'snapshot':
                continue

            self.progress.emit(i / nb_max * 100)
            self.log.emit("Loading publish {0}".format(name), "info")

            tmp = Publish(self.client, name, load=True,
                          storage=publish.get('Storage', "local"))
            publish_dict[name] = tmp

            for snapshot in tmp.publish_snapshots:
                try:
                    if self.cancelled:
                        self.terminate()
                    self.log.emit("Loading snapshot {0} of publish {1}".format(snapshot["Name"], name), "debug")
                    Publish._get_packages(self.client, "snapshots", snapshot["Name"])
                except Exception as e:
                    self.log.emit("Failed to fetch snapshot {0}: {1}".format(snapshot["Name"], e), "error")
            if self.cancelled:
                self.terminate()

        self.log.emit("Successfully loaded publishes", "success")
        self.data_manager.publish_dict = publish_dict
        self.data_manager.repo_dict = repo_dict


class AptlyThread(QThread):
    log = pyqtSignal(str, str)
    progress = pyqtSignal(int)

    def __init__(self, publish_name, data_manager):
        super(AptlyThread, self).__init__()
        self.publish = data_manager.get_publish(publish_name)
        self.data_manager = data_manager


class PublishThread(AptlyThread):
    def __init__(self, publish_name, data_manager, **kwargs):
        super(PublishThread, self).__init__(publish_name, data_manager)
        self.publish_name = publish_name
        self.package_list = kwargs.pop('package_list')
        self.component = kwargs.pop('component')
        merge = kwargs.pop('merge', False)

        self.old_snapshot = self.publish.get_component_snapshot(self.component)
        self.new_snapshot = self.data_manager.generate_snapshot_name(self.old_snapshot)

        if merge and self.component in self.publish.components.keys():
            self.package_list += self.publish._get_packages(self.data_manager.client, "snapshots", self.old_snapshot)
            self.package_list = list(set(self.package_list))

    def run(self):
        self.log.emit("Publishing {0}".format(self.publish_name), "info")
        try:
            if self.package_list:
                self.publish.create_snapshot_from_packages(self.package_list, self.new_snapshot, 'Snapshot created from GUI for component {}'.format(self.component))
                self.publish.replace_snapshot(self.component, self.new_snapshot)
                self.progress.emit(50)
                self.publish.do_publish(merge_snapshots=False)
                self.progress.emit(100)
        except Exception as e:
            self.log.emit(repr(e), "error")
            self.progress.emit(0)
            self.publish.replace_snapshot(self.component, self.old_snapshot)


class PublishComponentThread(AptlyThread):
    def __init__(self, publish_name, data_manager, **kwargs):
        super(PublishComponentThread, self).__init__(publish_name, data_manager)
        self.publish_name = publish_name
        self.source_publish = kwargs.pop('source_publish')
        self.components = kwargs.pop('components')
        self.source_publish = data_manager.get_publish(self.source_publish)

    def run(self):
        self.log.emit("Publishing {0}, components {1}".format(self.publish_name, self.components), "info")
        for component in self.components:
            self.publish.replace_snapshot(component, self.source_publish.get_component_snapshot(component))
        try:
            self.publish.do_publish(merge_snapshots=False)
            self.progress.emit(100)
        except Exception as e:
            self.log.emit(repr(e), "error")
            self.progress.emit(0)
