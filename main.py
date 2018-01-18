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

class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("python-aptly GUI")
        layout = QGridLayout()
        tabs = QTabWidget()
        tabs.addTab(SnapshotTab(), "Snapshot management")
        tabs.addTab(RepositoryTab(), "Repository management")
        tabs.addTab(PackagePromotion(), "Package Promotion")
        tabs.addTab(ComponentPromotion(), "Component Promotion")


        self.setLayout(layout)
        layout.addWidget(tabs)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = Window()
    window.show()

    sys.exit(app.exec_())
