#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from aptlygui.views.splash_screen import SplashScreen


def main():
    import sys

    app = QApplication(sys.argv)

    splash = SplashScreen()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
