#!/usr/bin/env python3

from PyQt5.QtWidgets import (QGridLayout, QProgressBar, QPushButton, QLabel, QLineEdit, QScrollArea, QDialog)

from views.main_window import Window
from workers.aptly_workers import DataThread
from data_manager import DataManager


class SplashScreen(QDialog):

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
