#!/usr/bin/env python3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import (QGridLayout, QFormLayout, QLabel, QPushButton, QWidget, QListView, QAbstractItemView,
                             QVBoxLayout)


class ListTab(QWidget):
    def __init__(self, data_manager, parent=None):
        super(ListTab, self).__init__(parent)
        self.data_manager = data_manager

        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.grid_layout = QGridLayout()

        self.package_label = QListView()
        self.package_label.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.model = QStandardItemModel(self.package_label)

        self.grid_layout.addWidget(self.package_label, 0, 0, 0, 0)

    def configure_layout(self):
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.grid_layout)
        self.setLayout(self.layout)

    def create_button(self, text, listener=None):
        new_button = QPushButton(text)
        new_button.setFixedWidth(new_button.sizeHint().width())
        if listener:
            new_button.clicked.connect(listener)
        return new_button

    def add_form_element(self, text, widget=None):
        self.form_layout.addRow(text, QLabel("") if widget is None else widget)

    def select_all(self):
        self.change_state(Qt.Checked)

    def unselect_all(self):
        self.change_state(Qt.Unchecked)

    def change_state(self, state):
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            item.setCheckState(state)

    def add_select_buttons(self):
        select_all_button = self.create_button("Select all", self.select_all)
        unselect_all_button = self.create_button("Unselect all", self.unselect_all)
        self.add_form_element("", select_all_button)
        self.add_form_element("", unselect_all_button)