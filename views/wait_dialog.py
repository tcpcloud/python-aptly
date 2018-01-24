#!/usr/bin/env python3


from PyQt5.QtWidgets import (QGridLayout, QLabel, QProgressBar, QDialog)
from workers.aptly_workers import (PublishThread, PublishComponentThread)

class WaitDialog(QDialog):

    def __init__(self, publish_name, data_manager, parent, **kwargs):
        super(WaitDialog, self).__init__(parent)

        self.layout = QGridLayout()
        self.progress_bar = QProgressBar(self)
        self.infoLabel = QLabel('Publishing {}'.format(publish_name))

        self.type = kwargs.pop('type', 'package')
        if self.type == "package":
            self.publishThread = PublishThread(publish_name, self.progress_bar, data_manager, **kwargs)
        else:
            self.publishThread = PublishComponentThread(publish_name, self.progress_bar, data_manager, **kwargs)

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("python-aptly GUI")
        self.setFixedSize(600, 200)
        self.setVisible(True)
        self.setModal(True)
        self.setLayout(self.layout)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.infoLabel)
        self.layout.addWidget(self.progress_bar)

        self.publishThread.start()
        self.publishThread.finished.connect(self.close)