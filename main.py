#!/usr/bin/env python3

from PyQt5.QtCore import QStringListModel, Qt, QThread
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QComboBox, QDataWidgetMapper,
                             QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QTextEdit, QWidget, QMainWindow,
                             QListView, QAbstractItemView, QAction, QTabWidget, QBoxLayout, QProgressBar, QDialog, QScrollArea, QSizePolicy)

from snapshot_tab import SnapshotTab
from repository_tab import RepositoryTab
from package_promotion import PackagePromotion
from component_promotion import ComponentPromotion
from data_manager import DataManager
from aptly.publisher import Publish
import time


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


class DataThread(QThread):

    def __init__(self, dataManager, bar, label):
        super(DataThread, self).__init__()
        self.client = dataManager.client
        self.data_manager = dataManager
        self.progress_dialog = bar
        self.label = label
        self.cancelled = False

    def run(self):
        publish_dict = {}

        try:
            publishes = self.client.do_get('/publish')
        except Exception as e:
            self.label.setText(e)
            self.terminate()

        i = 0
        nb_max = len(publishes)

        for publish in publishes:
            i += 1
            name = "{}{}{}".format(publish['Storage'] + ":" if publish['Storage']
                                   else "", publish['Prefix'] + "/" if
                                   publish['Prefix'] else "",
                                   publish['Distribution'])
            self.progress_dialog.setValue(i / nb_max * 100)
            # offen results in SIGSEGV
            #self.label.setText("Loading {}".format(name))
            tmp = Publish(self.client, name, load=True, storage=publish.get('Storage', "local"))
            publish_dict[name] = tmp

            for snapshot in tmp.publish_snapshots:
                try:
                    if self.cancelled:
                        self.terminate()
                    Publish._get_packages(self.client, "snapshots", snapshot["Name"])
                except Exception as e:
                    print("Failed to fetch snapshot")
            if self.cancelled:
                self.terminate()

        self.label.setText("Successfully loaded publishes")
        self.data_manager.publish_dict = publish_dict


class SplashScreen(QDialog):

    def load_main_window(self):
        if not self.dataThread.cancelled:
            self.setModal(False)
            self.window = Window(self.dataManager)
            self.window.show()
            self.close()

    def load_publish_connector(self):
        self.infoLabel.setText("Initializing connection")
        self.infoScroll.setWidget(self.infoLabel)
        self.progressBar.setValue(0)

        try:
            self.dataManager.create_client(self.urlEdit.text())
        except Exception as e:
            print(repr(e))
            self.infoLabel.setText(repr(e))
            self.infoScroll.setWidget(self.infoLabel)
            return

        self.dataThread = DataThread(self.dataManager, self.progressBar, self.infoLabel)
        self.dataThread.start()
        self.loadButton.disconnect()
        self.loadButton.setText("Cancel")
        self.loadButton.clicked.connect(self.abort_load)
        self.dataThread.finished.connect(self.load_main_window)

    def abort_load(self):
        self.dataThread.cancelled = True
        self.loadButton.setText("Load publish")
        self.loadButton.disconnect()
        self.loadButton.clicked.connect(self.load_publish_connector)

    def __init__(self):
        super(SplashScreen, self).__init__()
        self.layout = QGridLayout()
        self.progressBar = QProgressBar(self)
        self.urlLabel = QLabel("URL of Aptly :")
        self.urlEdit = QLineEdit("http://127.0.0.1:8089")
        self.loadButton = QPushButton("Connect to aptly")
        self.quitButton = QPushButton("Quit")
        self.dataManager = DataManager()
        self.infoLabel = QLabel("")
        self.infoScroll = QScrollArea()

        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("python-aptly GUI")
        self.setFixedSize(600, 200)
        self.setVisible(True)
        self.setLayout(self.layout)

        self.progressBar.setVisible(True)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)

        self.layout.addWidget(self.urlLabel)
        self.layout.addWidget(self.urlEdit)
        self.layout.addWidget(self.loadButton)
        self.layout.addWidget(self.progressBar)
        self.layout.addWidget(self.infoScroll)
        self.layout.addWidget(self.quitButton)

        self.loadButton.clicked.connect(self.load_publish_connector)
        self.quitButton.clicked.connect(self.close)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    splash = SplashScreen()

    sys.exit(app.exec_())
