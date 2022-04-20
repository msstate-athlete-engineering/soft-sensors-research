"""Contains the SensorServiceDriver class definition.

    SensorServiceDriver is an abstract class used by the SensorServiceItemModel to interact with different classes of
    sensing devices.

    Typical usage example:
    class MyCustomDriver(SensorServiceDriver):
        ...
"""

import enum
from typing import Any, List

from PyQt5.QtBluetooth import QBluetoothDeviceInfo, QBluetoothUuid
from PyQt5.QtCore import QObject, Qt, pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu

import SensorChannel as sc
import SensorServiceItem as ssi


class DriverState(enum.Enum):
    UnconnectedState = 0
    PreparingState = 1
    ReadyState = 2


class SensorServiceDriver(ssi.SensorServiceItem):
    """Base class used to implement a standard interface for interacting with devices to the SensorServiceItemModel.

    SensorServiceDrivers must implement a set of functionality in order to operate with the application. The abstract
    static methods deviceClass(), driverName(), matchUuid(), and supportedSamplingRates() must be implemented so that
    the SensorServiceItemModel is able to map devices' service UUIDs to specific drivers. At minimum, the instance
    methods samplingRate() and setSamplingRate(rate_hz: float) must be implemented. However, any other instance methods
    may be overridden to extend functionality.
    """

    # region Abstract Static Methods

    @staticmethod
    def deviceClass() -> str:
        """Returns the user-friendly class name of a device.

        Returns:
            String name of the device class. For example:

            "StretchSense V3"
            "Custom Hardware"
        """
        raise NotImplementedError

    @staticmethod
    def driverName() -> str:
        """Returns the user-friendly driver name to identify the driver being used.

        Returns:
            String driver name of the driver. For example:

            "SS16G3V197"
            "TI-REV1-DRIVER"
        """
        raise NotImplementedError

    @staticmethod
    def matchUuid() -> QBluetoothUuid:
        """Returns the GATT service UUID that will be used to match devices to appropriate drivers.

        Returns:
            QBluetoothUuid object storing the matchable GATT service UUID. For example:

            QBluetoothUuid("00001701-7374-7265-7563-6873656e7365")
        """
        raise NotImplementedError

    @staticmethod
    def supportedSamplingRates() -> List[float]:
        """Returns a list of sampling rates (in Hertz) supported by the device/driver.

        Returns:
            List of floating point numbers representing the sensor sampling rates (in Hz) that the device class
            supports. For example:

            [0.0, 25.0]
            [0.0, 1.0, 10.0, 100.0, 1000.0]
        """
        raise NotImplementedError

    # endregion

    # region Class Initializer

    def __init__(self, device_info: QBluetoothDeviceInfo, parent: QObject = None):
        """Initializes SensorServiceDriver with device info and a QObject parent.

        Upon creation, the driver will automatically initialize an internal QLowEnergyController and try to connect to
        the device. Additionally, this class will log important output or errors to the applications root-level Python
        logger.

        Args:
            device_info: QBluetoothDeviceInfo object created by a QBluetoothDeviceDiscoveryAgent
            parent: SensorServiceItemModel managing and monitoring the driver
        """
        super(SensorServiceDriver, self).__init__(parent=parent)

        # Basic data members
        self._contextMenu = self._initContextMenu()
        self._driverState: DriverState = DriverState.UnconnectedState
        self._sensorChannels: List[sc.SensorChannel] = []

        # UI Autorefresh Items
        self._uiRefreshTimer: QTimer = QTimer(parent=self)
        self._uiRefreshTimer.timeout.connect(self.__uiRefreshTimer_timeout)

    # endregion

    # region SensorServiceItem Implementation

    def contextMenu(self) -> QMenu:
        __doc__ = ssi.SensorServiceItem.contextMenu.__doc__  # Inherit docstring
        return self._contextMenu

    def data(self, role: Qt.ItemDataRole = None) -> Any:
        __doc__ = ssi.SensorServiceItem.data.__doc__  # Inherit docstring
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if self._driverState == DriverState.ReadyState:
                return f"{type(self).deviceClass()} [{self.samplingRate()} Hz]"
            return f"{type(self).deviceClass()} [{self.deviceAddress()}]"
        elif role == Qt.DecorationRole:
            if self._driverState == DriverState.PreparingState:
                return QIcon("icons/preparing.png")
            if self._driverState == DriverState.ReadyState:
                return QIcon("icons/prepared.png")
            else:
                return QIcon("icons/unconnected.png")
        elif role == Qt.EditRole:
            return self.data(role=Qt.DisplayRole)
        elif role == Qt.CheckStateRole:
            if len(self._sensorChannels) == 0:
                return Qt.Unchecked
            elif all([s_ch.data(Qt.CheckStateRole) == Qt.Checked for s_ch in self._sensorChannels]):
                return Qt.Checked
            elif all([s_ch.data(Qt.CheckStateRole) == Qt.Unchecked for s_ch in self._sensorChannels]):
                return Qt.Unchecked
            else:
                return Qt.PartiallyChecked

        return None

    def flags(self) -> Qt.ItemFlags:
        __doc__ = ssi.SensorServiceItem.flags.__doc__  # Inherit docstring
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def setData(self, value: Any, role: Qt.ItemDataRole = None):
        __doc__ = ssi.SensorServiceItem.setData.__doc__  # Inherit docstring
        if role == Qt.CheckStateRole:
            return all([s_ch.setData(value, role) for s_ch in self._sensorChannels])
        return False

    # endregion

    # region Abstract Instance Methods

    def deviceAddress(self):
        raise NotImplementedError

    def deviceName(self):
        raise NotImplementedError

    def deviceServices(self):
        raise NotImplementedError

    def samplingRate(self) -> float:
        raise NotImplementedError

    def setSamplingRate(self, rate_hz: float) -> None:
        raise NotImplementedError

    # endregion

    # region Instance Methods

    def clearRecordedData(self) -> None:
        for s_ch in self._sensorChannels:
            s_ch.clear_samples()

    def epoch(self):
        return self.parent().epoch()

    # Getters

    def sensorChannels(self) -> List[sc.SensorChannel]:
        return self._sensorChannels

    def uiRefreshRate(self) -> float:
        return 1000 // self._uiRefreshTimer.interval()

    # Setters
    def setUiRefreshRate(self, rate_hz) -> None:
        self._uiRefreshTimer.setInterval(1000 // rate_hz)
        self._uiRefreshTimer.stop() if rate_hz == 0.0 else self._uiRefreshTimer.start()

    # endregion

    # region Protected Instance Methods

    def _addSensorChannel(self, sensor_channel: sc.SensorChannel) -> None:
        self.rowsAboutToBeInserted.emit(len(self._sensorChannels), len(self._sensorChannels))
        self._sensorChannels.append(sensor_channel)
        self.rowsInserted.emit(len(self._sensorChannels), len(self._sensorChannels))

    def _clearSensorChannels(self) -> None:
        last_idx = len(self._sensorChannels) - 1
        self.rowsAboutToBeRemoved.emit(0, last_idx)
        self._sensorChannels = []
        self.rowsRemoved.emit(0, last_idx)

    def _removeSensorChannel(self, sensor_channel: sc.SensorChannel) -> None:
        idx = self._sensorChannels.index(sensor_channel)
        self.rowsAboutToBeRemoved.emit(idx, idx)
        self._sensorChannels.remove(sensor_channel)
        self.rowsRemoved.emit(idx, idx)

    def _setDriverState(self, state: DriverState):
        self._driverState = state
        self.dataChanged.emit(False, [Qt.DecorationRole])

    def _initContextMenu(self) -> QMenu:
        # Initialize context menu
        context_menu = QMenu("Service Driver")

        # Initialize actions
        connect_action = QAction("Connect", self)
        connect_action.setData("connect")
        context_menu.addAction(connect_action)

        disconnect_action = QAction("Disconnect", self)
        disconnect_action.setData("disconnect")
        context_menu.addAction(disconnect_action)

        # Sampling rate menu
        context_menu.addSeparator()
        sampling_menu = QMenu("Sampling Rate", context_menu)
        sampling_menu.setObjectName("sampling_menu")
        context_menu.addMenu(sampling_menu)

        # Add supported sampling rates to sampling rate menu
        check_icon = QIcon("icons/check.svg")
        for rate_hz in type(self).supportedSamplingRates():
            action = QAction(check_icon, f"{rate_hz} Hz{' (Off)' if rate_hz == 0.0 else ''}", sampling_menu)
            action.setData(rate_hz)
            sampling_menu.addAction(action)

        # Change the enabled state of different actions based on driver state
        context_menu.aboutToShow.connect(
            lambda: connect_action.setEnabled(self._driverState == DriverState.UnconnectedState))
        context_menu.aboutToShow.connect(
            lambda: disconnect_action.setEnabled(
                self._driverState == DriverState.PreparingState or self._driverState == DriverState.ReadyState))
        context_menu.aboutToShow.connect(
            lambda: sampling_menu.setEnabled(self._driverState == DriverState.ReadyState))

        # Put a check by the currently selected sampling rate
        context_menu.aboutToShow.connect(self.__context_menu_aboutToShow)

        # Upon selected a sampling rate, tell the driver to use that sampling rate
        sampling_menu.triggered.connect(lambda act: self.setSamplingRate(act.data()))

        return context_menu

    # endregion

    # region Signals

    dataChanged = pyqtSignal(bool, list, name="dataChanged")
    error = pyqtSignal(str, name="error")
    rowsAboutToBeInserted = pyqtSignal(int, int, name="rowsAboutToBeInserted")
    rowsAboutToBeRemoved = pyqtSignal(int, int, name="rowsAboutToBeRemoved")
    rowsInserted = pyqtSignal(int, int, name="rowsInserted")
    rowsRemoved = pyqtSignal(int, int, name="rowsRemoved")

    # endregion

    # region Slots

    @pyqtSlot(name="__context_menu_aboutToShow")
    def __context_menu_aboutToShow(self):
        sampling_menu: QMenu = self._contextMenu.findChild(QMenu, "sampling_menu")
        current_sampling_rate = self.samplingRate()
        for action in sampling_menu.actions():
            action.setIconVisibleInMenu(action.data() == current_sampling_rate)

    # UI Timer
    @pyqtSlot(name="__uiRefreshTimer_timeout")
    def __uiRefreshTimer_timeout(self):
        if len(self._sensorChannels) > 0:
            for s_ch in self.sensorChannels():
                s_ch.updatePlotDataItem()
            self.dataChanged.emit(True, [Qt.DisplayRole])

    # endregion
