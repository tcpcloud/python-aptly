from PyQt5.QtWidgets import (QProgressBar, QTextEdit)
from PyQt5.QtCore import pyqtSlot


class QCustomProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        super(QCustomProgressBar, self).__init__(*args, **kwargs)
        self.setVisible(True)
        self.setMaximum(100)
        self.setValue(0)

    @pyqtSlot(int)
    def on_progress_received(self, value):
        self.setValue(value)


class QLogConsole(QTextEdit):
    def __init__(self, *args, **kwargs):
        super(QLogConsole, self).__init__(*args, **kwargs)
        self.setReadOnly(True)

    @pyqtSlot(str, str)
    def on_log_received(self, msg, severity="info"):
        self.__getattribute__(severity)(msg)

    def write(self, msg, color):
        if not color:
            self.insertPlainText("{0}\n".format(msg))
        else:
            self.insertHtml("<font color={0}>{1}</font><br>".format(color, msg))
        self.ensureCursorVisible()

    def info(self, msg):
        self.write(msg, "blue")

    def debug(self, msg):
        self.write(msg, "gray")

    def error(self, msg):
        self.write(msg, "red")

    def success(self, msg):
        self.write(msg, "green")
