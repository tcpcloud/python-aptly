#!/usr/bin/env python3
import datetime
import time
from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QComboBox, QDataWidgetMapper,
                             QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QTextEdit, QWidget, QMainWindow,
                             QListView, QAbstractItemView, QAction, QTabWidget)

from aptly.publisher import Publish, PublishManager
from aptly.client import Aptly
from data_manager import DataManager


class PackagePromotion(QWidget):
    def __init__(self, dataManager,parent=None):
        super(PackagePromotion, self).__init__(parent)

        self.dataManager = dataManager

        # initialize widgets
        self.componentBox = QComboBox()
        self.componentLabel = QLabel("Component")
        self.sourcePublishBox = QComboBox()
        self.sourcePublishLabel = QLabel("Source")
        self.targetPublishBox = QComboBox()
        self.targetPublishLabel = QLabel("Target")
        self.publishButton = QPushButton("Promote")

        self.packageLabel = QListView()
        self.packageLabel.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # place widget in the layout
        layout = QGridLayout()
        layout.addWidget(self.sourcePublishBox, 0, 0, 1, 1)
        layout.addWidget(self.componentBox, 0, 1, 1, 1)
        layout.addWidget(self.targetPublishBox, 0, 2, 1, 1)
        layout.addWidget(self.packageLabel, 1, 1, 2, 1)
        layout.addWidget(self.publishButton, 1, 2, 1, 1)
        self.setLayout(layout)

        # initialize data
        self.model = QStandardItemModel(self.packageLabel)
        self.fillPublishBox()
        self.recreatePackageBox()
        # controllers
        self.sourcePublishBox.currentIndexChanged.connect(self.updateSnapshotBox)
        self.componentBox.currentIndexChanged.connect(self.recreatePackageBox)
        self.publishButton.clicked.connect(self.updatePublish)

    def loadSnapshot(self, name):
        return Publish.get_packages(self.dataManager.get_client(), "snapshots", name)

    def updatePublish(self):
        targetPublish = self.dataManager.get_publish(self.targetPublishBox.currentText())
        targetPublish.load()
        packageList = set()
        # find a better way to get packages
        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                packageList.add(currentItem.text())

        component = self.componentBox.currentText()
        oldSnapshotName = targetPublish.components[component][0]
        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
        newSnapshotName = DataManager.generate_snapshot_name(oldSnapshotName)

        old_packages = targetPublish._get_packages(self.dataManager.get_client(), "snapshots", oldSnapshotName)
        for package in old_packages:
            packageList.add(package)

        targetPublish.create_snapshots_from_packages(list(packageList), newSnapshotName, 'Snapshot created from GUI for component {}'.format(component))
        targetPublish.replace_snapshot(component, newSnapshotName)
        targetPublish.do_publish(recreate=False, merge_snapshots=False)


    def fillPublishBox(self):
        self.sourcePublishBox.clear()
        self.targetPublishBox.clear()
        publishes = self.dataManager.get_publish_list()
        for publish in publishes:
            self.sourcePublishBox.addItem(publish)
            self.targetPublishBox.addItem(publish)
        self.sourcePublishBox.update()
        self.targetPublishBox.update()
        # update snapshot box
        if len(publishes) > 0:
            self.updateSnapshotBox()

    def updateSnapshotBox(self):
        name = self.sourcePublishBox.currentText()
        currentPublish = self.dataManager.get_publish(name)
        currentPublish.load()
        self.componentBox.clear()
        for component in sorted(list(currentPublish.components.keys())):
            self.componentBox.addItem(component)
        self.componentBox.update()

    def recreatePackageBox(self):
        self.model.removeRows(0, self.model.rowCount())
        component = self.componentBox.currentText()
        publish =self.sourcePublishBox.currentText()

        # empty sometimes?
        if not component:
            return

        packages = self.dataManager.get_package_from_publish_component(publish, component)

        for package in packages:
            item = QStandardItem(package)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.packageLabel.setModel(self.model)

    def reloadComponent(self):
        if len(self.dataManager.get_publish_list()) > 0:
            self.updateSnapshotBox()

