#!/usr/bin/env python3

from PyQt5.QtCore import QStringListModel, Qt, QThread
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QComboBox, QDataWidgetMapper,
                             QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QTextEdit, QWidget, QMainWindow,
                             QListView, QAbstractItemView, QAction, QTabWidget, QBoxLayout, QProgressBar, QDialog)

from SnapshotTab import SnapshotTab
from RepositoryTab import RepositoryTab
from package_promotion import PackagePromotion
from component_promotion import ComponentPromotion
from data_manager import DataManager
from aptly.publisher import Publish
import time

class Window(QMainWindow):

    def __init__(self, dataManager, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("python-aptly GUI")


        mainWidget = QWidget(self)
        layout = QGridLayout()
        self.tabs = QTabWidget()
        self.tabs.addTab(SnapshotTab(dataManager), "Snapshot management")
        self.tabs.addTab(RepositoryTab(dataManager), "Repository management")
        self.tabs.addTab(PackagePromotion(dataManager), "Package Promotion")
        self.tabs.addTab(ComponentPromotion(dataManager), "Component Promotion")


        mainWidget.setLayout(layout)
        layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.foo)
        self.setCentralWidget(mainWidget)

        menubar = QMenuBar()
        menubar.addMenu('shit')
        menubar.addMenu('shit2')

    def foo(self, item):
        t = self.tabs.currentWidget()
        t.reloadComponent()





class DataThread(QThread):

    def __init__(self, dataManager, bar, label):
        super(DataThread, self).__init__()
        self.client = dataManager.client
        self.dataManager = dataManager
        self.progressDialog = bar
        self.label = label


    def run(self):
        publish_dict = {}
        publishes = self.client.do_get('/publish')
        i = 0
        nbMax = len(publishes)
        self.progressDialog.setValue(0)

        for publish in publishes:
            i += 1

            name = "{}{}{}".format(publish['Storage'] + ":" if publish['Storage']
                                   else "", publish['Prefix'] + "/" if
                                   publish['Prefix'] else "",
                                   publish['Distribution'])
            self.progressDialog.setValue(i / nbMax * 100)
            self.label.setText("Loading {}".format(name))
            tmp = Publish(self.client, name, load=True, storage=publish.get('Storage', "local"))
            publish_dict[name] = tmp

            for snapshot in tmp.publish_snapshots:
                try:
                    Publish._get_packages(self.client, "snapshots", snapshot["Name"])
                except Exception as e:
                    print("Failed to fetch snapshot")

        self.label.setText("Successfully loaded publishes")
        self.dataManager.publish_dict = publish_dict


class SplashScreen(QDialog):

    def loadPublishConnector(self):
        dataThread = DataThread(self.dataManager, self.progress, self.label)
        dataThread.run()

        self.setModal(False)
        self.window = Window(self.dataManager)
        self.window.show()
        self.close()

    def __init__(self):
        dataManager = DataManager()
        dataManager.create_client("http://127.0.0.1:8089")
        #dataManager.create_client("http://apt.mirantis.net:8084")
        super(SplashScreen, self).__init__()
        self.setWindowTitle("python-aptly GUI")
        layout = QGridLayout()
        loadButton = QPushButton("Load publishes")
        self.label = QLabel("")
        progress = QProgressBar(self)
        layout.addWidget(loadButton)
        layout.addWidget(progress)
        layout.addWidget(self.label)
        progress.setVisible(True)
        progress.setMaximum(100)
        progress.setValue(0)
        self.setLayout(layout)
        self.setVisible(True)
        self.progress = progress
        self.client = dataManager.client
        self.dataManager = dataManager
        self.setFixedSize(600,150)
        loadButton.clicked.connect(self.loadPublishConnector)



if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    splash = SplashScreen()

    sys.exit(app.exec_())
