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
        self.repoBox = QComboBox()
        self.deleteButton = QPushButton("Delete")
        self.snapshotButton = QPushButton("Snapshot")
        self.minimalSnapshotButton = QPushButton("Minimal snapshot")
        self.packageLabel = QListView()
        self.packageLabel.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # place widget in the layout
        layout = QGridLayout()
        layout.addWidget(self.repoBox, 0, 0, 1, 1)
        layout.addWidget(self.deleteButton, 0, 1, 1, 1)
        layout.addWidget(self.snapshotButton, 0, 2, 1, 1)
        layout.addWidget(self.minimalSnapshotButton, 1, 2, 1, 1)
        layout.addWidget(self.packageLabel, 1, 1, 2, 1)
        self.setLayout(layout)

        # initialize datas
        self.model = QStandardItemModel(self.packageLabel)
        self.client = self.createClient()
        self.repoDictionnary = {}
        # controllers
        self.loadRepository()
        self.repoBox.currentIndexChanged.connect(self.updateList)
        self.deleteButton.clicked.connect(self.removePackage)

    def createClient(self):
        return Aptly("http://127.0.0.1:8089", dry=False, timeout=600)

    def loadRepository(self):
        repos = Publish._get_repositories(self.client)
        repo_list = []
        for repo in repos:
            repo_list.append(repo["Name"])
        for repo in sorted(repo_list):
            self.repoBox.addItem(repo)
        self.repoBox.update()
        self.updateList()

    def updateList(self):
        self.model.removeRows(0, self.model.rowCount())
        currentRepo = self.repoBox.currentText()
        if currentRepo == "":
            return
        if currentRepo not in self.repoDictionnary.keys():
            print(currentRepo)
            self.repoDictionnary[currentRepo] = sorted(Publish._get_packages(self.client, "repos", currentRepo))

        if self.repoDictionnary[currentRepo]:
            for package in self.repoDictionnary[currentRepo]:
                item = QStandardItem(package)
                item.setCheckable(True)
                item.setCheckState(Qt.Unchecked)
                self.model.appendRow(item)
            self.packageLabel.setModel(self.model)


    def removePackage(self):
        packageList = []
        repoName = self.repoBox.currentText()
        self.repoDictionnary[repoName] = []
        for index in range(self.model.rowCount()):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                packageList.append(currentItem.text())
            else:
                self.repoDictionnary[repoName].append(currentItem.text())
        print(packageList)
        self.client.do_delete('/repos/%s/packages' % repoName, data={'PackageRefs': packageList})
        self.updateList()

    def createMinimalSnapshot(self):
        # TODO
        i = 10

    def createSnapshot(self):
        # TODO
        i = 100

    # TODO: disable buttons if no packages...






