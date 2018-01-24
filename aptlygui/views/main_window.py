from PyQt5.QtWidgets import (QGridLayout, QMenuBar, QWidget, QMainWindow, QTabWidget)

from aptlygui.views.snapshot_tab import SnapshotTab
from aptlygui.views.repository_tab import RepositoryTab
from aptlygui.views.package_promotion import PackagePromotion
from aptlygui.views.component_promotion import ComponentPromotion


class Window(QMainWindow):

    def __init__(self, dataManager, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("python-aptly GUI")

        main_widget = QWidget(self)
        layout = QGridLayout()
        self.tabs = QTabWidget()
        self.tabs.addTab(SnapshotTab(dataManager), "Snapshot management")
        self.tabs.addTab(RepositoryTab(dataManager), "Repository management")
        self.tabs.addTab(PackagePromotion(dataManager), "Package Promotion")
        self.tabs.addTab(ComponentPromotion(dataManager), "Component Promotion")

        main_widget.setLayout(layout)
        layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.foo)
        self.setCentralWidget(main_widget)

        menubar = QMenuBar()
        menubar.addMenu('shit')
        menubar.addMenu('shit2')

    def foo(self, item):
        t = self.tabs.currentWidget()
        t.reload_component()
