import logging

from PyQt5 import uic
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QWidget, QTextEdit

LoggingDialogUI, LoggingDialogBase = uic.loadUiType("LoggingDialog.ui")


class LoggingDialog(LoggingDialogBase, LoggingDialogUI):
    def __init__(self, parent: QWidget = None):
        # uic boilerplate
        LoggingDialogBase.__init__(self, parent=parent)
        self.setupUi(self)

        # Setup logging handler
        self.__textEditHandler = LoggingDialog.TextEditHandler(self.logTextEdit)
        logging.getLogger().addHandler(self.__textEditHandler)

    class TextEditHandler(logging.Handler):
        def __init__(self, text_edit: QTextEdit, level=logging.NOTSET):
            super(LoggingDialog.TextEditHandler, self).__init__(level=level)

            # Setup text edit
            self.__text_edit = text_edit

        def emit(self, record: logging.LogRecord):
            self.__text_edit.moveCursor(QTextCursor.End)
            self.__text_edit.insertPlainText(record.getMessage() + "\n")
