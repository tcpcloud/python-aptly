#!/usr/bin/env python3

from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QComboBox, QDataWidgetMapper,
                             QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QTextEdit, QWidget, QMainWindow,
                             QListView, QAbstractItemView, QAction, QTabWidget)

from aptly.publisher import Publish, PublishManager
from aptly.client import Aptly
from data_manager import DataManager

class SnapshotTab(QWidget):
    def __init__(self, dataManager,parent=None):
        self.dataManager = dataManager
        super(SnapshotTab, self).__init__(parent)

        # initialize widgets
        self.componentBox = QComboBox()
        self.publishBox = QComboBox()
        self.publishButton = QPushButton("Publish")
        self.reloadButton = QPushButton("Reload")
        self.packageLabel = QListView()
        self.packageLabel.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # place widget in the layout
        layout = QGridLayout()
        layout.addWidget(self.publishBox, 0, 0, 1, 1)
        layout.addWidget(self.componentBox, 0, 1, 1, 1)
        layout.addWidget(self.publishButton, 0, 2, 1, 1)
        layout.addWidget(self.packageLabel, 1, 1, 2, 1)
        layout.addWidget(self.reloadButton, 1, 2, 1, 1)
        self.setLayout(layout)

        # initialize datas
        self.model = QStandardItemModel(self.packageLabel)
        self.fillPublishBox()
        self.recreatePackageBox()
        # controllers
        self.publishBox.currentIndexChanged.connect(self.updateSnapshotBox)
        self.componentBox.currentIndexChanged.connect(self.recreatePackageBox)
        self.publishButton.clicked.connect(self.updatePublish)

    def loadSnapshot(self, name):
        return Publish._get_packages(self.dataManager.get_client(), "snapshots", name)

    def updatePublish(self):
        publish_name = self.publishBox.currentText()
        currentPublish = self.dataManager.get_publish(publish_name)
        packageList = []
        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                packageList.append(currentItem.text())

        # TODO: create function for snapshot name?
        component = self.componentBox.currentText()
        oldSnapshotName = currentPublish.components[component][0]
        newSnapshotName = DataManager.generate_snapshot_name(oldSnapshotName)
        currentPublish.create_snapshots_from_packages(packageList, newSnapshotName, 'Snapshot created from GUI for component {}'.format(component))
        currentPublish.replace_snapshot(component, newSnapshotName)
        currentPublish.do_publish(recreate=False, merge_snapshots=False)

    def fillPublishBox(self):
        self.publishBox.clear()
        publishes = self.dataManager.get_publish_list()
        for publish in publishes:
            self.publishBox.addItem(publish)
        if len(publishes) > 0:
            self.publishBox.update()
            self.updateSnapshotBox()

    def updateSnapshotBox(self):
        name = self.publishBox.currentText()
        currentPublish = self.dataManager.get_publish(name)
        currentPublish.load()
        self.componentBox.clear()
        for component in sorted(list(currentPublish.components.keys())):
            self.componentBox.addItem(component)
        self.componentBox.update()

    def recreatePackageBox(self):
        self.model.removeRows(0, self.model.rowCount())
        component = self.componentBox.currentText()
        currentPublish = self.publishBox.currentText()

        # empty sometimes?
        if not component:
            return

        packages = self.dataManager.get_package_from_publish_component(currentPublish, component)

        for package in packages:
            item = QStandardItem(package)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.packageLabel.setModel(self.model)

    def reloadComponent(self):
        if len(self.dataManager.get_publish_list()) > 0:
            self.updateSnapshotBox()
            self.recreatePackageBox()

