#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QPushButton, QWidget, QListView, QAbstractItemView)

from aptly.publisher import Publish, PublishManager


class RepositoryTab(QWidget):

    def __init__(self, data_manager, parent=None):
        super(RepositoryTab, self).__init__(parent)

        self.data_manager = data_manager
        # initialize widgets
        self.repo_box = QComboBox()
        self.delete_button = QPushButton("Delete")
        self.package_label = QListView()
        self.package_label.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # place widget in the layout
        layout = QGridLayout()
        layout.addWidget(self.repo_box, 0, 0, 1, 1)
        layout.addWidget(self.delete_button, 0, 1, 1, 1)
        layout.addWidget(self.package_label, 1, 1, 2, 1)
        self.setLayout(layout)

        # initialize data
        self.model = QStandardItemModel(self.package_label)
        self.repo_dictionary = {}
        # controllers
        self.load_repository()
        self.repo_box.currentIndexChanged.connect(self.update_list)
        self.delete_button.clicked.connect(self.remove_package)

    def load_repository(self):
        repos = Publish._get_repositories(self.data_manager.get_client())
        repo_list = []
        for repo in repos:
            repo_list.append(repo["Name"])
        for repo in sorted(repo_list):
            self.repo_box.addItem(repo)
        self.repo_box.update()
        self.update_list()

    def update_list(self):
        self.model.removeRows(0, self.model.rowCount())
        current_repo = self.repo_box.currentText()
        if current_repo == "":
            return
        if current_repo not in self.repo_dictionary.keys():
            self.repo_dictionary[current_repo] = sorted(Publish._get_packages(self.data_manager.get_client(), "repos",
                                                                              current_repo))

        if self.repo_dictionary[current_repo]:
            for package in self.repo_dictionary[current_repo]:
                item = QStandardItem(package)
                item.setCheckable(True)
                item.setCheckState(Qt.Unchecked)
                self.model.appendRow(item)
            self.package_label.setModel(self.model)

    def remove_package(self):
        package_list = []
        repo_name = self.repo_box.currentText()
        self.repo_dictionary[repo_name] = []
        for index in range(self.model.rowCount()):
            current_item = self.model.item(index)
            if current_item and current_item.checkState() != 0:
                package_list.append(current_item.text())
            else:
                self.repo_dictionary[repo_name].append(current_item.text())
        print(package_list)
        self.data_manager.get_client().do_delete('/repos/%s/packages' % repo_name, data={'PackageRefs': package_list})
        self.update_list()

    # TODO: disable buttons if no packages...
    def reload_component(self):
        return
