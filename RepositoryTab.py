#!/usr/bin/env python3


# copy from dev.py

from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QComboBox, QDataWidgetMapper,
                             QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QTextEdit, QWidget, QMainWindow,
                             QListView, QAbstractItemView, QAction, QTabWidget)

from aptly.publisher import Publish, PublishManager
from aptly.client import Aptly


class RepositoryTab(QWidget):
    def __init__(self, parent=None):
        super(RepositoryTab, self).__init__(parent)

        # initialize widgets
        self.test = QTabWidget()
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
        self.client = self.createClient()
        self.publishDic = self.preLoadPublishes()
        self.fillPublishBox()
        self.recreatePackageBox()
        # controllers
        self.publishBox.currentIndexChanged.connect(self.updateSnapshotBox)
        self.componentBox.currentIndexChanged.connect(self.recreatePackageBox)
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
        # check if deep copy of shallow copy
        currentPublish = self.publishDic[self.publishBox.currentText()]
        packageList = []
        # find a better way to get packages
        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                packageList.append(currentItem.text())
                # WE NEED TO RELOAD PUBLISH FOR REAL TO NOT PUBLISH SHIT?

        # TODO: create function for snapshot name?
        component = self.componentBox.currentText()
        oldSnapshotName = currentPublish.components[component][0]
        newSnapshotName = "{}-{}".format(oldSnapshotName, "gui")
        currentPublish.create_snapshots_from_packages(packageList, newSnapshotName, 'Snapshot created from GUI for component {}'.format(component))
        currentPublish.replace_snapshot(component, newSnapshotName)
        currentPublish.do_publish(recreate=False, merge_snapshots=False)
        # TODO: check the dictionnary is also updated


    def fillPublishBox(self):
        self.publishBox.clear()
        for publish in sorted(self.publishDic.keys()):
            self.publishBox.addItem(publish)
        self.publishBox.update()
        # update snapshot box
        self.updateSnapshotBox()

    def updateSnapshotBox(self):
        name = self.publishBox.currentText()
        currentPublish = self.publishDic[name]
        currentPublish.load()
        self.componentBox.clear()
        for component in sorted(list(currentPublish.components.keys())):
            self.componentBox.addItem(component)
        self.componentBox.update()

    def recreatePackageBox(self):
        self.model.removeRows(0, self.model.rowCount())
        component = self.componentBox.currentText()
        currentPublish = self.publishDic[self.publishBox.currentText()]

        # empty sometimes?
        if not component:
            return

        packages = sorted(currentPublish._get_packages(self.client, "snapshots", currentPublish.components[component][0]))

        for package in packages:
            item = QStandardItem(package)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.packageLabel.setModel(self.model)

