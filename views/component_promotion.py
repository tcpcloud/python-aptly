#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QLabel, QPushButton, QWidget, QListView, QAbstractItemView)

from aptly.publisher import Publish
from views.wait_dialog import WaitDialog


class ComponentPromotion(QWidget):
    def __init__(self, data_manager, parent=None):
        super(ComponentPromotion, self).__init__(parent)

        self.data_manager = data_manager
        # initialize widgets
        self.component_label = QLabel("List of components")
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
        layout.addWidget(self.component_label, 0, 1, 1, 1)
        layout.addWidget(self.target_publish_box, 0, 2, 1, 1)
        layout.addWidget(self.package_label, 1, 1, 2, 1)
        layout.addWidget(self.publish_button, 1, 2, 1, 1)
        self.setLayout(layout)

        # initialize data
        self.model = QStandardItemModel(self.package_label)
        self.fill_publish_box()
        # controllers
        self.source_publish_box.currentIndexChanged.connect(self.recreate_package_box)
        self.publish_button.clicked.connect(self.update_publish)

    def load_snapshot(self, name):
        return Publish.get_packages(self.data_manager.get_client(), "snapshots", name)

    def update_publish(self):
        target_publish = self.target_publish_box.currentText()
        source_publish = self.source_publish_box.currentText()
        component_list = []

        for index in reversed(range(self.model.rowCount())):
            current_item = self.model.item(index)
            if current_item and current_item.checkState() != 0:
                component_list.append(current_item.text())

        wait_dialog = WaitDialog(target_publish, self.data_manager, self, source_publish=source_publish,
                                 components=component_list, type="components")

    def fill_publish_box(self):
        self.source_publish_box.clear()
        self.target_publish_box.clear()
        publishes = self.data_manager.get_publish_list()
        for publish in publishes:
            self.source_publish_box.addItem(publish)
            self.target_publish_box.addItem(publish)
        self.source_publish_box.update()
        self.target_publish_box.update()
        if len(publishes) > 0:
            self.recreate_package_box()

    def recreate_package_box(self):
        self.model.removeRows(0, self.model.rowCount())
        current_publish = self.data_manager.get_publish(self.source_publish_box.currentText())
        current_publish.load()
        components = current_publish.components.keys()

        for component in components:
            item = QStandardItem(component)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.package_label.setModel(self.model)

    def reload_component(self):
        if len(self.data_manager.get_publish_list()) > 0:
            self.recreate_package_box()
