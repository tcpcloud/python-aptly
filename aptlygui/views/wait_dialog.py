#!/usr/bin/env python3


from PyQt5.QtWidgets import (QGridLayout, QDialog, QPushButton)
from aptlygui.widgets import (QCustomProgressBar, QLogConsole)
from aptlygui.workers.aptly_workers import (PublishThread, PublishComponentThread)


class WaitDialog(QDialog):

    def __init__(self, publish_name, data_manager, parent, **kwargs):
        super(WaitDialog, self).__init__(parent)

        self.layout = QGridLayout()
        self.progress_bar = QCustomProgressBar(self)
        self.logConsole = QLogConsole()
        self.action_button = QPushButton("Process")
        self.quit_button = QPushButton("Exit")

        self.type = kwargs.pop('type', 'package')

        if self.type == "package":
            self.publishThread = PublishThread(publish_name, data_manager, **kwargs)
        else:
            self.publishThread = PublishComponentThread(publish_name, data_manager, **kwargs)

        self.publishThread.progress.connect(self.progress_bar.on_progress_received)
        self.publishThread.log.connect(self.logConsole.on_log_received)
        self.publishThread.finished.connect(self.handle_worker)

        self.action_button.clicked.connect(self.start_action)
        self.quit_button.clicked.connect(self.close)

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("python-aptly GUI")
        self.setFixedSize(600, 200)
        self.setVisible(True)
        self.setModal(True)
        self.setLayout(self.layout)

        self.layout.addWidget(self.action_button)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.logConsole)
        self.layout.addWidget(self.quit_button)

    def start_action(self):
        self.action_button.setDisabled(True)
        self.publishThread.start()

    def handle_worker(self):
        if self.progress_bar.value() == 100:
            self.close()
