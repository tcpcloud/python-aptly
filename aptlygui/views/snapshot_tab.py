#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QPushButton, QWidget, QListView, QAbstractItemView)

from aptlygui.views.wait_dialog import WaitDialog


class SnapshotTab(QWidget):
    def __init__(self, dataManager, parent=None):
        self.dataManager = dataManager
        super(SnapshotTab, self).__init__(parent)

        # initialize widgets
        self.component_box = QComboBox()
        self.publish_box = QComboBox()
        self.publish_button = QPushButton("Publish")
        self.reload_button = QPushButton("Reload")
        self.package_label = QListView()
        self.package_label.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # place widget in the layout
        layout = QGridLayout()
        layout.addWidget(self.publish_box, 0, 0, 1, 1)
        layout.addWidget(self.component_box, 0, 1, 1, 1)
        layout.addWidget(self.publish_button, 0, 2, 1, 1)
        layout.addWidget(self.package_label, 1, 1, 2, 1)
        layout.addWidget(self.reload_button, 1, 2, 1, 1)
        self.setLayout(layout)

        # initialize data
        self.model = QStandardItemModel(self.package_label)
        self.fill_publish_box()
        self.recreate_package_box()
        # controllers
        self.publish_box.currentIndexChanged.connect(self.update_snapshot_box)
        self.component_box.currentIndexChanged.connect(self.recreate_package_box)
        self.publish_button.clicked.connect(self.update_publish)

    def update_publish(self):
        publish_name = self.publish_box.currentText()
        package_list = []
        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                package_list.append(currentItem.text())

        # TODO: create function for snapshot name?
        component = self.component_box.currentText()
        waitDialog = WaitDialog(publish_name, self.dataManager, self, component=component, package_list=package_list)

    def fill_publish_box(self):
        self.publish_box.clear()
        publishes = self.dataManager.get_publish_list()
        for publish in publishes:
            self.publish_box.addItem(publish)
        if len(publishes) > 0:
            self.publish_box.update()
            self.update_snapshot_box()

    def update_snapshot_box(self):
        name = self.publish_box.currentText()
        current_publish = self.dataManager.get_publish(name)
        self.component_box.clear()
        for component in sorted(list(current_publish.components.keys())):
            self.component_box.addItem(component)
        self.component_box.update()

    def recreate_package_box(self):
        self.model.removeRows(0, self.model.rowCount())
        component = self.component_box.currentText()
        current_publish = self.publish_box.currentText()

        # empty sometimes?
        if not component:
            return

        packages = self.dataManager.get_package_from_publish_component(current_publish, component)

        for package in packages:
            item = QStandardItem(package)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.package_label.setModel(self.model)

    def reload_component(self):
        if len(self.dataManager.get_publish_list()) > 0:
            self.update_snapshot_box()
            self.recreate_package_box()
