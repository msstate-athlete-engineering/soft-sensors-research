import datetime as dt
import logging
from typing import Any

from PyQt5.QtBluetooth import QBluetoothDeviceDiscoveryAgent, QBluetoothDeviceInfo
from PyQt5.QtCore import QObject, QUuid, pyqtSlot, QAbstractItemModel, QModelIndex, pyqtSignal, Qt

import SensorChannel as sc
import SensorServiceDriver as ssd
import drivers.SS16G3V197 as SS16G3V197
import drivers.AthEngDCMk1 as AthEngDCMk1


class SensorServiceItemModel(QAbstractItemModel):
    SERVICE_DRIVERS = [SS16G3V197.SS16G3V197, AthEngDCMk1.AthEngDCMk1]  # TODO: use __subclass_init__ instead?

    UI_SENSOR_REFRESH_RATE_HZ = 5.0  # Rate in Hz to refresh the UI sensor values and plot

    # region Class Initializer

    def __init__(self, parent: QObject = None):
        # Use superclass initializer
        super(SensorServiceItemModel, self).__init__(parent)

        # Build service driver mappings
        self.__serviceDriverMap = {QUuid(driver.matchUuid()): driver for driver in
                                   SensorServiceItemModel.SERVICE_DRIVERS}

        # List for storing active service drivers
        self.__activeServiceDrivers = []

        # Initialize Bluetooth discovery
        self.__deviceDiscoveryAgent = None
        self.__initBluetoothDiscovery()

        # Store recording and timing state
        self.__epoch = dt.datetime.now()
        self.__recording = False

    # endregion

    # region QAbstractItemModel Implementation

    def index(self, row: int, column: int, parent: QModelIndex = None, *args, **kwargs):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if parent is None or not parent.isValid():
            return self.createIndex(row, column, self.__activeServiceDrivers[row])
        elif isinstance(parent.internalPointer(), ssd.SensorServiceDriver):
            return self.createIndex(row, column, parent.internalPointer().sensorChannels()[row])

        return QModelIndex()

    def hasIndex(self, row: int, column: int, parent: QModelIndex = None, *args, **kwargs):
        if parent is None or not parent.isValid():
            return row < len(self.__activeServiceDrivers) and column == 0
        elif isinstance(parent.internalPointer(), ssd.SensorServiceDriver):
            return row < len(parent.internalPointer().sensorChannels()) and column == 0

        return False

    def parent(self, index: QModelIndex = None):
        if isinstance(index.internalPointer(), ssd.SensorServiceDriver):
            return QModelIndex()
        if isinstance(index.internalPointer(), sc.SensorChannel):
            parent = index.internalPointer().parent()
            parent_row = self.__activeServiceDrivers.index(parent)
            return self.createIndex(parent_row, 0, parent)

        return QModelIndex()

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        if parent is None or not parent.isValid():
            return len(self.__activeServiceDrivers)
        elif isinstance(parent.internalPointer(), ssd.SensorServiceDriver):
            return len(parent.internalPointer().sensorChannels())

        return 0

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs):
        return 1

    def data(self, index: QModelIndex, role: int = None):
        if isinstance(index.internalPointer(), ssd.SensorServiceDriver):
            return index.internalPointer().data(role)
        elif isinstance(index.internalPointer(), sc.SensorChannel):
            return index.internalPointer().data(role)

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = None):
        if not index.isValid():
            return False

        return index.internalPointer().setData(value, role)

    def flags(self, index: QModelIndex):
        if index.isValid():
            return index.internalPointer().flags()

    # endregion

    # region Instance Methods

    def clearRecordedData(self):
        for driver in self.__activeServiceDrivers:
            driver.clearRecordedData()

    def epoch(self) -> dt.datetime:
        return self.__epoch

    def selectedChannels(self):
        checked = [s_ch.internalPointer() for s_ch in
                   self.match(self.index(0, 0), Qt.CheckStateRole, Qt.Checked, hits=-1,
                              flags=(Qt.MatchExactly | Qt.MatchWrap | Qt.MatchRecursive))
                   if isinstance(s_ch.internalPointer(), sc.SensorChannel)]
        return checked

    def plotDataItems(self):
        checked = self.selectedChannels()
        return [s_ch.plot_data_item for s_ch in checked]

    def recording(self) -> bool:
        if len(self.__activeServiceDrivers) == 0:
            return False
        return self.__recording

    def setEpoch(self, epoch: dt.datetime) -> None:
        self.__epoch = epoch

    def startDiscovery(self, timeout: int = 3000):  # default timeout = 3 seconds
        if not self.__deviceDiscoveryAgent.isActive():
            logging.info(f"Starting Bluetooth Low Energy device discovery ({timeout / 1000}s).")
            self.__deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(timeout)
            self.__deviceDiscoveryAgent.start(QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(2))  # LowEnergyMethod
            self.discoveringChanged.emit(True)

    def startRecordingAllServices(self):
        if len(self.__activeServiceDrivers) == 0:
            self.__recording = False
            return

        self.setEpoch(dt.datetime.now())
        self.__recording = True
        self.recordingChanged.emit(self.recording())

    def stopDiscovery(self):
        if self.__deviceDiscoveryAgent.isActive():
            logging.info("Bluetooth Low Energy device discovery stopped.")
            self.__deviceDiscoveryAgent.stop()
            self.discoveringChanged.emit(False)

    def stopRecordingAllServices(self):
        self.__recording = False
        self.recordingChanged.emit(self.recording())
        for s_ch in self.selectedChannels():
            s_ch.updatePlotDataItem()

    # endregion

    # region Private Instance Methods

    def __initBluetoothDiscovery(self):
        self.__deviceDiscoveryAgent = QBluetoothDeviceDiscoveryAgent(self)
        self.__deviceDiscoveryAgent.deviceDiscovered.connect(self.__deviceDiscoveryAgent_deviceDiscovered)
        self.__deviceDiscoveryAgent.finished.connect(lambda: self.discoveringChanged.emit(False))
        self.__deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(3000)  # 3 seconds

    # endregion

    # region Signals

    discoveringChanged = pyqtSignal(bool, name="discoveringChanged")
    recordingChanged = pyqtSignal(bool, name="recordingChanged")

    # endregion

    # region Slots

    @pyqtSlot(bool, list, name="__activeServiceDriver_dataChanged")
    def __activeServiceDriver_dataChanged(self, children: bool, roles: list):
        row = self.__activeServiceDrivers.index(self.sender())
        idx = self.index(row, 0, None)
        self.dataChanged.emit(idx, idx, roles)

        if children:
            top_left = self.index(0, 0, idx)
            bottom_right = self.index(len(idx.internalPointer().sensorChannels()) - 1, 0, idx)
            self.dataChanged.emit(top_left, bottom_right, roles)

    @pyqtSlot(str, name="__activeServiceDriver_error")
    def __activeServiceDriver_error(self, error_msg: str):
        if self.recording():
            self.stopRecordingAllServices()
        # TODO: Display error message?

    @pyqtSlot(int, int, name="__activeServiceDriver_rowsAboutToBeInserted")
    def __activeServiceDriver_rowsAboutToBeInserted(self, first: int, last: int):
        row = self.__activeServiceDrivers.index(self.sender())
        idx = self.index(row, 0, None)
        self.beginInsertRows(idx, first, last)

    @pyqtSlot(int, int, name="__activeServiceDriver_rowsAboutToBeRemoved")
    def __activeServiceDriver_rowsAboutToBeRemoved(self, first: int, last: int):
        row = self.__activeServiceDrivers.index(self.sender())
        idx = self.index(row, 0, None)
        self.beginRemoveRows(idx, first, last)

    @pyqtSlot(int, int, name="__activeServiceDriver_rowsInserted")
    def __activeServiceDriver_rowsInserted(self, first: int, last: int):
        self.endInsertRows()

    @pyqtSlot(int, int, name="__activeServiceDriver_rowsRemoved")
    def __activeServiceDriver_rowsRemoved(self, first: int, last: int):
        self.endRemoveRows()

    # TODO: Clean up this function
    @pyqtSlot(QBluetoothDeviceInfo, name="deviceDiscovered")
    def __deviceDiscoveryAgent_deviceDiscovered(self, device_info: QBluetoothDeviceInfo):
        # Match corresponding GATT service UUIDs
        uuids = [QUuid(uuid) for uuid in device_info.serviceUuids()[0]]
        matched_uuids = set(uuids) & set(self.__serviceDriverMap.keys())

        # Initialize service drivers for each service
        addr_uuid_pairs = [(drv.deviceAddress(), type(drv).matchUuid()) for drv in self.__activeServiceDrivers]
        for uuid in matched_uuids:
            # Skip duplicate entries
            if (device_info.address(), uuid) in addr_uuid_pairs:
                continue

            logging.info(f"Recognized service {uuid.toString()} on device {device_info.address().toString()}"
                         f" ({device_info.name()}).")

            # Create driver and calculate its new index in __activeServiceDrivers
            driver = self.__serviceDriverMap[uuid](device_info, parent=self)
            driver.setUiRefreshRate(SensorServiceItemModel.UI_SENSOR_REFRESH_RATE_HZ)
            driver.dataChanged.connect(self.__activeServiceDriver_dataChanged)
            driver.error.connect(self.__activeServiceDriver_error)
            driver.rowsAboutToBeInserted.connect(self.__activeServiceDriver_rowsAboutToBeInserted)
            driver.rowsAboutToBeRemoved.connect(self.__activeServiceDriver_rowsAboutToBeRemoved)
            driver.rowsInserted.connect(self.__activeServiceDriver_rowsInserted)
            driver.rowsRemoved.connect(self.__activeServiceDriver_rowsRemoved)
            new_idx = len(self.__activeServiceDrivers)

            # Notify model of new row
            self.beginInsertRows(QModelIndex(), new_idx, new_idx)
            self.__activeServiceDrivers.append(driver)
            self.endInsertRows()

    # endregion
