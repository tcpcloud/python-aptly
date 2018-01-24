#!/usr/bin/env python3

from aptly.client import Aptly
from aptly.publisher import Publish
from PyQt5.QtWidgets import (QApplication, QComboBox, QDataWidgetMapper,
                             QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QTextEdit, QWidget, QMainWindow,
                             QListView, QAbstractItemView, QAction, QTabWidget, QBoxLayout, QProgressBar, QDialog, QScrollArea, QSizePolicy)

from PyQt5.QtCore import (pyqtSignal, QDataStream, QMutex, QMutexLocker,
        QThread, QWaitCondition)

import time
import datetime

class WaitDialog(QDialog):

    def __init__(self, publish_name, data_manager, parent, **kwargs):
        super(WaitDialog, self).__init__(parent)

        self.layout = QGridLayout()
        self.progress_bar = QProgressBar(self)
        self.infoLabel = QLabel('Publishing {}'.format(publish_name))

        self.type = kwargs.pop('type', 'package')
        if self.type == "package":
            self.publishThread = PublishThread(publish_name, self.progress_bar, data_manager, **kwargs)
        else:
            self.publishThread = PublishComponentThread(publish_name, self.progress_bar, data_manager, **kwargs)

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("python-aptly GUI")
        self.setFixedSize(600, 200)
        self.setVisible(True)
        self.setModal(True)
        self.setLayout(self.layout)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.infoLabel)
        self.layout.addWidget(self.progress_bar)

        self.publishThread.start()
        self.publishThread.finished.connect(self.close)


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
        time.sleep(2)

        try:
            if self.package_list:
                self.publish.create_snapshot_from_packages(self.package_list, self.new_snapshot,
                                                           'Snapshot created from GUI for component {}'.format(
                                                                self.component))
                self.publish.replace_snapshot(self.component, self.new_snapshot)
                self.progress_bar.setValue(50)
        except Exception as e:
            # TODO: Add label?
            print(repr(e))
            self.progress_bar.setValue(0)
            self.publish.replace_snapshot(self.component, self.old_snapshot)

        time.sleep(2)
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

