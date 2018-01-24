#!/usr/bin/env python3


from PyQt5.QtWidgets import (QGridLayout, QDialog)
from aptlygui.widgets import (QCustomProgressBar, QLogConsole)
from aptlygui.workers.aptly_workers import (PublishThread, PublishComponentThread)


class WaitDialog(QDialog):

    def __init__(self, publish_name, data_manager, parent, **kwargs):
        super(WaitDialog, self).__init__(parent)

        self.layout = QGridLayout()
        self.progress_bar = QCustomProgressBar(self)
        self.logConsole = QLogConsole()

        self.type = kwargs.pop('type', 'package')
        if self.type == "package":
            self.publishThread = PublishThread(publish_name, data_manager, **kwargs)
        else:
            self.publishThread = PublishComponentThread(publish_name, data_manager, **kwargs)

        self.publishThread.progress.connect(self.progressBar.on_progress_received)
        self.dataThread.log.connect(self.logConsole.on_log_received)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("python-aptly GUI")
        self.setFixedSize(600, 200)
        self.setVisible(True)
        self.setModal(True)
        self.setLayout(self.layout)
        self.layout.addWidget(self.infoLabel)
        self.layout.addWidget(self.progress_bar)

        self.publishThread.start()
        self.publishThread.finished.connect(self.close)
