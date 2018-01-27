#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QLabel, QPushButton, QWidget, QListView, QAbstractItemView)

from aptly.publisher import Publish
from aptlygui.views.wait_dialog import WaitDialog


class PackagePromotion(QWidget):
    def __init__(self, data_manager, parent=None):
        super(PackagePromotion, self).__init__(parent)

        self.data_manager = data_manager

        # initialize widgets
        self.component_box = QComboBox()
        self.component_label = QLabel("Component")
        self.source_publish_box = QComboBox()
        self.source_publish_label = QLabel("Source")
        self.target_publish_box = QComboBox()
        self.target_publish_label = QLabel("Target")
        self.publish_button = QPushButton("Promote")

        self.package_label = QListView()
        self.package_label.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # place widget in the layout
        layout = QGridLayout()
        layout.addWidget(self.source_publish_box, 0, 0, 1, 1)
        layout.addWidget(self.component_box, 0, 1, 1, 1)
        layout.addWidget(self.target_publish_box, 0, 2, 1, 1)
        layout.addWidget(self.package_label, 1, 1, 2, 1)
        layout.addWidget(self.publish_button, 1, 2, 1, 1)
        self.setLayout(layout)

        # initialize data
        self.model = QStandardItemModel(self.package_label)
        self.fill_publish_box()
        self.recreate_package_box()
        # controllers
        self.source_publish_box.currentIndexChanged.connect(self.update_snapshot_box)
        self.component_box.currentIndexChanged.connect(self.recreate_package_box)
        self.publish_button.clicked.connect(self.update_publish)

    def load_snapshot(self, name):
        return Publish.get_packages(self.data_manager.get_client(), "snapshots", name)

    def update_publish(self):
        target_publish_name = self.target_publish_box.currentText()
        component = self.component_box.currentText()

        package_list = []
        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                package_list.append(currentItem.text())

        wait_dialog = WaitDialog(target_publish_name, self.data_manager, self, component=component,
                                 package_list=package_list, merge=True)

    def fill_publish_box(self):
        self.source_publish_box.clear()
        self.target_publish_box.clear()
        publishes = self.data_manager.get_publish_list()
        for publish in publishes:
            self.source_publish_box.addItem(publish)
            self.target_publish_box.addItem(publish)
        self.source_publish_box.update()
        self.target_publish_box.update()
        # update snapshot box
        if len(publishes) > 0:
            self.update_snapshot_box()

    def update_snapshot_box(self):
        name = self.source_publish_box.currentText()
        current_publish = self.data_manager.get_publish(name)
        self.component_box.clear()
        for component in sorted(list(current_publish.components.keys())):
            self.component_box.addItem(component)
        self.component_box.update()

    def recreate_package_box(self):
        self.model.removeRows(0, self.model.rowCount())
        component = self.component_box.currentText()
        publish = self.source_publish_box.currentText()

        # empty sometimes?
        if not component:
            return

        packages = self.data_manager.get_package_from_publish_component(publish, component)

        for package in packages:
            item = QStandardItem(package)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.package_label.setModel(self.model)

    def reload_component(self):
        if len(self.data_manager.get_publish_list()) > 0:
            self.update_snapshot_box()
