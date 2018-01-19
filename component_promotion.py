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


class ComponentPromotion(QWidget):
    def __init__(self, dataManager,parent=None):
        super(ComponentPromotion, self).__init__(parent)

        self.dataManager = dataManager
        # initialize widgets
        self.componentLabel = QLabel("List of components")
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
        layout.addWidget(self.componentLabel, 0, 1, 1, 1)
        layout.addWidget(self.targetPublishBox, 0, 2, 1, 1)
        layout.addWidget(self.packageLabel, 1, 1, 2, 1)
        layout.addWidget(self.publishButton, 1, 2, 1, 1)
        self.setLayout(layout)

        # initialize data
        self.model = QStandardItemModel(self.packageLabel)
        self.fillPublishBox()
        self.recreatePackageBox()
        # controllers
        self.sourcePublishBox.currentIndexChanged.connect(self.recreatePackageBox)
        self.publishButton.clicked.connect(self.updatePublish)

    def loadSnapshot(self, name):
        return Publish.get_packages(self.dataManager.get_client(), "snapshots", name)

    def updatePublish(self):
        targetPublish = self.dataManager.get_publish(self.targetPublishBox.currentText())
        targetPublish.load()

        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                component = currentItem.text()
                newSnapshot = self.dataManager.get_publish(self.sourcePublishBox.currentText()).components[component][0]
                targetPublish.replace_snapshot(component, newSnapshot)
        targetPublish.do_publish(merge_snapshots=False)

    def fillPublishBox(self):
        self.sourcePublishBox.clear()
        self.targetPublishBox.clear()
        for publish in self.dataManager.get_publish_list():
            self.sourcePublishBox.addItem(publish)
            self.targetPublishBox.addItem(publish)
        self.sourcePublishBox.update()
        self.targetPublishBox.update()

    def recreatePackageBox(self):
        self.model.removeRows(0, self.model.rowCount())
        currentPublish = self.dataManager.get_publish(self.sourcePublishBox.currentText())
        currentPublish.load()
        components = currentPublish.components.keys()

        for component in components:
            item = QStandardItem(component)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.packageLabel.setModel(self.model)

    def reloadComponent(self):
        self.recreatePackageBox()
        return
