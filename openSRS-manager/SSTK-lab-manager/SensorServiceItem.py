from typing import Any

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QMenu


class SensorServiceItem(QObject):

    # region Class Initializer

    def __init__(self, parent: QObject = None):
        super(SensorServiceItem, self).__init__(parent=parent)

    # endregion

    # region Abstract Instance Methods

    def contextMenu(self) -> QMenu:
        raise NotImplementedError

    def data(self, role: Qt.ItemDataRole = None) -> Any:
        raise NotImplementedError

    def flags(self) -> Qt.ItemFlags:
        raise NotImplementedError

    def setData(self, value: Any, role: Qt.ItemDataRole = None) -> bool:
        raise NotImplementedError

    # endregion

    # region Instance Methods

    def recording(self) -> bool:
        return self.parent().recording()

    # endregion
