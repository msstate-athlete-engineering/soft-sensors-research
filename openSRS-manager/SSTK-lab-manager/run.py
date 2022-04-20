import logging
import sys

from PyQt5.QtWidgets import QApplication

import MainWindow as mw

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Initialize application
    app = QApplication(sys.argv)
    mainWindow = mw.MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

