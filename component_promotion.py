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
    def __init__(self, parent=None):
        super(ComponentPromotion, self).__init__(parent)

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
        self.client = self.createClient()
        self.publishDic = self.preLoadPublishes()
        self.fillPublishBox()
        self.recreatePackageBox()
        # controllers
        self.sourcePublishBox.currentIndexChanged.connect(self.recreatePackageBox)
        self.publishButton.clicked.connect(self.updatePublish)


    def createClient(self):
        return Aptly("http://127.0.0.1:8089", dry=False, timeout=600)

    def preLoadPublishes(self):
        publishList = {}
        publishes = self.client.do_get('/publish')
        for publish in publishes:
            name = "{}{}{}".format(publish['Storage'] + ":" if publish['Storage']
                                   else "", publish['Prefix'] + "/" if
                                   publish['Prefix'] else "",
                                   publish['Distribution'])
            publishList[name] = Publish(self.client, name, load=False, storage=publish.get('Storage', "local"))
        return publishList

    def loadSnapshot(self, name):
        return Publish.get_packages(self.client, "snapshots", name)

    def updatePublish(self):
        targetPublish = self.publishDic[self.targetPublishBox.currentText()]
        targetPublish.load()
        # find a better way to get packages
        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                component = currentItem.text()
                newSnapshot = self.publishDic[self.sourcePublishBox.currentText()].components[component][0]
                targetPublish.replace_snapshot(component, newSnapshot)
        targetPublish.do_publish(recreate=False, merge_snapshots=False)

    def fillPublishBox(self):
        self.sourcePublishBox.clear()
        self.targetPublishBox.clear()
        for publish in sorted(self.publishDic.keys()):
            self.sourcePublishBox.addItem(publish)
            self.targetPublishBox.addItem(publish)
        self.sourcePublishBox.update()
        self.targetPublishBox.update()

    def recreatePackageBox(self):
        self.model.removeRows(0, self.model.rowCount())
        currentPublish = self.publishDic[self.sourcePublishBox.currentText()]
        currentPublish.load()
        components = currentPublish.components.keys()

        for component in components:
            item = QStandardItem(component)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.packageLabel.setModel(self.model)

