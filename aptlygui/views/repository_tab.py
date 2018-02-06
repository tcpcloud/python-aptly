#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QComboBox

from aptlygui.widgets.list_tab import ListTab


class RepositoryTab(ListTab):

    def __init__(self, data_manager, parent=None):
        super(RepositoryTab, self).__init__(data_manager, parent)

        self.repo_box = QComboBox()

        delete_button = self.create_button("Delete", self.remove_package)

        self.add_form_element("Repository", self.repo_box)
        self.add_form_element("")
        self.add_form_element("Action", delete_button)
        self.add_select_buttons()
        self.add_form_element("Packages")

        # controllers
        self.load_repository()
        self.repo_box.currentIndexChanged.connect(self.update_list)

        self.configure_layout()

    def load_repository(self):
        repos = self.data_manager.client.do_get('/repos')
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

        if self.data_manager.repo_dict[current_repo]:
            for package in self.data_manager.repo_dict[current_repo]:
                item = QStandardItem(package)
                item.setCheckable(True)
                item.setCheckState(Qt.Unchecked)
                self.model.appendRow(item)
            self.package_label.setModel(self.model)

    def remove_package(self):
        package_list = []
        repo_name = self.repo_box.currentText()
        self.data_manager.repo_dict[repo_name] = []
        for index in range(self.model.rowCount()):
            current_item = self.model.item(index)
            if current_item and current_item.checkState() != 0:
                package_list.append(current_item.text())
            else:
                self.data_manager.repo_dict[repo_name].append(current_item.text())
        self.data_manager.get_client().do_delete('/repos/%s/packages' % repo_name, data={'PackageRefs': package_list})
        self.update_list()

    def reload_component(self):
        return
