#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QLabel, QPushButton, QWidget, QListView, QAbstractItemView)

from aptly.publisher import Publish
from aptlygui.views.wait_dialog import WaitDialog
from aptlygui.views.list_tab import ListTab


class ComponentPromotion(ListTab):
    def __init__(self, data_manager, parent=None):
        super(ComponentPromotion, self).__init__(data_manager, parent)

        self.component_label = QLabel("List of components")
        self.source_publish_box = QComboBox()
        self.target_publish_box = QComboBox()
        publish_button = self.create_button("Promote", self.update_publish)

        self.add_form_element("Source publish", self.source_publish_box)
        self.add_form_element("Target publish", self.target_publish_box)
        self.add_form_element("")
        self.add_form_element("Action", publish_button)
        self.add_select_buttons()
        self.add_form_element("Components")

        self.fill_publish_box()

        self.source_publish_box.currentIndexChanged.connect(self.recreate_package_box)
        self.configure_layout()

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
