#!/usr/bin/env python3

from PyQt5.QtCore import QThread
from aptly.publisher import Publish
from PyQt5.QtCore import pyqtSignal


class DataThread(QThread):
    log = pyqtSignal(str, str)

    def __init__(self, dataManager, bar):
        super(DataThread, self).__init__()
        self.client = dataManager.client
        self.data_manager = dataManager
        self.progress_dialog = bar
        self.cancelled = False

    def run(self):
        publish_dict = {}

        try:
            publishes = self.client.do_get('/publish')
        except Exception as e:
            self.log.emit(e, "error")
            self.terminate()

        i = 0
        nb_max = len(publishes)

        for publish in publishes:
            i += 1
            name = "{}{}{}".format(publish['Storage'] + ":"
                                   if publish['Storage']
                                   else "", publish['Prefix'] + "/" if
                                   publish['Prefix'] else "",
                                   publish['Distribution'])

            self.progress_dialog.setValue(i / nb_max * 100)
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


class AptlyThread(QThread):
    def __init__(self, publish_name, progress_bar, data_manager):
        super(AptlyThread, self).__init__()
        self.publish = data_manager.get_publish(publish_name)
        self.progress_bar = progress_bar
        self.data_manager = data_manager


class PublishThread(AptlyThread):
    def __init__(self, publish_name, progress_bar, data_manager, **kwargs):
        super(PublishThread, self).__init__(publish_name, progress_bar, data_manager)
        self.package_list = kwargs.pop('package_list')
        self.component = kwargs.pop('component')
        merge = kwargs.pop('merge', False)

        self.old_snapshot = self.publish.get_component_snapshot(self.component)
        self.new_snapshot = self.data_manager.generate_snapshot_name(self.old_snapshot)

        if merge:
            self.package_list += self.publish._get_packages(self.data_manager.client, "snapshots", self.old_snapshot)
            self.package_list = list(set(self.package_list))

    def run(self):

        try:
            if self.package_list:
                self.publish.create_snapshot_from_packages(self.package_list, self.new_snapshot, 'Snapshot created from GUI for component {}'.format(self.component))
                self.publish.replace_snapshot(self.component, self.new_snapshot)
                self.progress_bar.setValue(50)
        except Exception as e:
            # TODO: Add label?
            print(repr(e))
            self.progress_bar.setValue(0)
            self.publish.replace_snapshot(self.component, self.old_snapshot)

        self.publish.do_publish(merge_snapshots=False)
        self.progress_bar.setValue(100)


class PublishComponentThread(AptlyThread):
    def __init__(self, publish_name, progress_bar, data_manager, **kwargs):
        super(PublishComponentThread, self).__init__(publish_name, progress_bar, data_manager)
        self.source_publish = kwargs.pop('source_publish')
        self.components = kwargs.pop('components')
        self.source_publish = data_manager.get_publish(self.source_publish)

    def run(self):
        for component in self.components:
            self.publish.replace_snapshot(component, self.source_publish.get_component_snapshot(component))
        self.publish.do_publish(merge_snapshots=False)
        self.progress_bar.setValue(100)
