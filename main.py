#!/usr/bin/env python3

from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QComboBox, QDataWidgetMapper,
                             QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QTextEdit, QWidget, QMainWindow,
                             QListView, QAbstractItemView, QAction, QTabWidget, QBoxLayout)

from SnapshotTab import SnapshotTab
from RepositoryTab import RepositoryTab
from package_promotion import PackagePromotion
from component_promotion import ComponentPromotion
from data_manager import DataManager

class Window(QWidget):


    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("python-aptly GUI")

        dataManager = DataManager()
        dataManager.create_client("http://127.0.0.1:8089")

        layout = QGridLayout()
        self.tabs = QTabWidget()
        self.tabs.addTab(SnapshotTab(dataManager), "Snapshot management")
        self.tabs.addTab(RepositoryTab(dataManager), "Repository management")
        self.tabs.addTab(PackagePromotion(dataManager), "Package Promotion")
        self.tabs.addTab(ComponentPromotion(dataManager), "Component Promotion")

        self.setLayout(layout)
        layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.foo)

    def foo(self, item):
        t = self.tabs.currentWidget()
        print(type(t))

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = Window()
    window.show()

    sys.exit(app.exec_())
