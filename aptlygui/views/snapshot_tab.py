#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QFormLayout, QPushButton, QWidget, QListView, QAbstractItemView, QVBoxLayout, QCheckBox, QLabel)

from aptlygui.widgets.list_tab import ListTab
from aptlygui.views.wait_dialog import WaitDialog


class SnapshotTab(ListTab):
    def __init__(self, data_manager, parent=None):
        super(SnapshotTab, self).__init__(data_manager, parent)

        # initialize widgets
        self.component_box = QComboBox()
        self.publish_box = QComboBox()

        publish_button = self.create_button("Publish", self.update_publish)

        self.add_form_element("Publish", self.publish_box)
        self.add_form_element("Component", self.component_box)
        self.add_form_element("")
        self.add_form_element("Action", publish_button)
        self.add_select_buttons()
        self.add_form_element("Packages")

        self.fill_publish_box()
        self.recreate_package_box()

        self.publish_box.currentIndexChanged.connect(self.update_snapshot_box)
        self.component_box.currentIndexChanged.connect(self.recreate_package_box)
        self.configure_layout()

    def update_publish(self):
        publish_name = self.publish_box.currentText()
        package_list = []
        for index in reversed(range(self.model.rowCount())):
            currentItem = self.model.item(index)
            if currentItem and currentItem.checkState() != 0:
                package_list.append(currentItem.text())

        component = self.component_box.currentText()
        waitDialog = WaitDialog(publish_name, self.data_manager, self, component=component, package_list=package_list)

    def fill_publish_box(self):
        self.publish_box.clear()
        publishes = self.data_manager.get_publish_list()
        for publish in publishes:
            self.publish_box.addItem(publish)
        if len(publishes) > 0:
            self.publish_box.update()
            self.update_snapshot_box()

    def update_snapshot_box(self):
        name = self.publish_box.currentText()
        current_publish = self.data_manager.get_publish(name)
        self.component_box.clear()
        for component in sorted(list(current_publish.components.keys())):
            self.component_box.addItem(component)
        self.component_box.update()

    def recreate_package_box(self):
        self.model.removeRows(0, self.model.rowCount())
        component = self.component_box.currentText()
        current_publish = self.publish_box.currentText()

        if not component:
            return

        packages = self.data_manager.get_package_from_publish_component(current_publish, component)

        for package in packages:
            item = QStandardItem(package)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.model.appendRow(item)
        self.package_label.setModel(self.model)

    def reload_component(self):
        if len(self.data_manager.get_publish_list()) > 0:
            self.update_snapshot_box()
            self.recreate_package_box()
