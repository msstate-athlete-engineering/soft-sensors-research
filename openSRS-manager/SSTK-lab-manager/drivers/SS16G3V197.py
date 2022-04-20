import datetime as dt
import logging
import struct
from typing import List

from PyQt5.QtBluetooth import QBluetoothDeviceInfo, QLowEnergyService, QBluetoothUuid, QLowEnergyCharacteristic
from PyQt5.QtCore import QObject, pyqtSlot, QByteArray, Qt

import SensorChannel as sc
import SensorServiceDriver as ssd


class SS16G3V197(ssd.SensorServiceDriver):

    # region SensorServiceDriver Static Implementation

    @staticmethod
    def defaultSamplingRate() -> float:
        return 25.0

    @staticmethod
    def deviceClass() -> str:
        return "StretchSense V3"

    @staticmethod
    def driverName() -> str:
        return "SS16G3V197"

    @staticmethod
    def matchUuid() -> QBluetoothUuid:
        return QBluetoothUuid("00001701-7374-7265-7563-6873656e7365")

    @staticmethod
    def supportedSamplingRates() -> List[float]:
        return [0.0, 25.0]

    # endregion

    # Private Constants

    __DATA_CHAR_UUID = QBluetoothUuid("00001702-7374-7265-7563-6873656e7365")
    __FREQ_CHAR_UUID = QBluetoothUuid("00001705-7374-7265-7563-6873656e7365")

    # endregion

    # region Class Initializer

    def __init__(self, device_info: QBluetoothDeviceInfo, parent: QObject = None):
        self.__dataCharacteristic = None
        self.__freqCharacteristic = None
        self.__samplingEnabled = False

        # Use superclass initializer
        super(SS16G3V197, self).__init__(device_info, parent=parent)

    # endregion

    # region SensorServiceDriver Implementation

    def samplingRate(self) -> float:
        if not self.__samplingEnabled:
            return 0.0

        if self._lowEnergyService is None:
            raise RuntimeError("BLE service controller not initialized")

        return 25.0

    def setSamplingRate(self, rate_hz: float) -> None:
        if rate_hz not in type(self).supportedSamplingRates():
            raise ValueError("sampling rate not supported")

        if self._lowEnergyService is None:
            raise RuntimeError("BLE service controller not initialized")

        if self.samplingRate() == rate_hz:
            return  # Don't do anything if sampling rate not changed.

        logging.info(f"Setting {self._lowEnergyController.remoteAddress().toString()} "
                     f"({self._lowEnergyController.remoteName()}) "
                     f"sampling rate to {rate_hz} Hz.")

        if rate_hz == 0.0:
            self.__unsubscribeDataNotifications()
            return

        self._lowEnergyService.writeCharacteristic(self.__freqCharacteristic, struct.pack("B", 0x00))
        self.__subscribeDataNotifications()

    # endregion

    # region Private Helper Methods

    def __subscribeDataNotifications(self):
        data_desc = self.__dataCharacteristic.descriptor(
            QBluetoothUuid(QBluetoothUuid.ClientCharacteristicConfiguration))
        if not data_desc.isValid():
            logging.error(f"No Client Characteristic Configuration Descriptor found for characteristic"
                          f"{self.__dataCharacteristic.uuid().toString()} on device "
                          f"{self._lowEnergyController.remoteAddress().toString()} "
                          f"({self._lowEnergyController.remoteName()}).")

        logging.info(f"Enabled sampling for {self._lowEnergyController.remoteAddress().toString()} "
                     f"({self._lowEnergyController.remoteName()}).")

        self._lowEnergyService.characteristicChanged.connect(self.__dataCharacteristic_characteristicChanged)
        self._lowEnergyService.writeDescriptor(data_desc, b'\x01\x00')
        self.__samplingEnabled = True
        self.dataChanged.emit(False, [Qt.DisplayRole])

    def __unsubscribeDataNotifications(self):
        data_desc = self.__dataCharacteristic.descriptor(
            QBluetoothUuid(QBluetoothUuid.ClientCharacteristicConfiguration))
        if not data_desc.isValid():
            logging.error(f"No Client Characteristic Configuration Descriptor found for characteristic"
                          f"{self.__dataCharacteristic.uuid().toString()} on device "
                          f"{self._lowEnergyController.remoteAddress().toString()} "
                          f"({self._lowEnergyController.remoteName()}).")

        logging.info(f"Disabled sampling for {self._lowEnergyController.remoteAddress()} "
                     f"({self._lowEnergyController.remoteName()}).")

        self._lowEnergyService.characteristicChanged.disconnect(self.__dataCharacteristic_characteristicChanged)
        self._lowEnergyService.writeDescriptor(data_desc, b'\x00\x00')
        self.__samplingEnabled = False
        self.dataChanged.emit(False, [Qt.DisplayRole])

        for s_ch in self._sensorChannels:
            s_ch.setCurrentValue(None, None)

    # endregion

    # region Slots

    @pyqtSlot(QLowEnergyCharacteristic, QByteArray, name="__dataCharacteristic_characteristicChanged")
    def __dataCharacteristic_characteristicChanged(self, char: QLowEnergyCharacteristic, data: QByteArray):
        if char.uuid() == self.__dataCharacteristic.uuid():
            parsed_data = [x * 0.1 for x in struct.unpack(">HHHHHHHHHH", data)]

            timestamp = None
            if self.parent().recording():
                if self._sensorChannels[0].currentValue()[0] is None:  # First sample case
                    timestamp = dt.datetime.now() - self.parent().epoch()
                else:  # Subsequent sample case
                    timestamp = self._sensorChannels[0].currentValue()[0] + \
                                dt.timedelta(seconds=1.0 / self.samplingRate())

            for i in range(len(parsed_data)):
                self._sensorChannels[i].setCurrentValue(timestamp, parsed_data[i])

    @pyqtSlot(QBluetoothUuid, name="_lowEnergyController_serviceDiscovered")
    def _lowEnergyController_serviceDiscovered(self, service_uuid: QBluetoothUuid):
        if service_uuid == type(self).matchUuid():
            self._lowEnergyService = self._lowEnergyController.createServiceObject(service_uuid)
            self._lowEnergyService.error.connect(self.__lowEnergyService_error)
            self._lowEnergyService.stateChanged.connect(self._lowEnergyService_stateChanged)
            self._lowEnergyService.discoverDetails()

    @pyqtSlot(QLowEnergyService.ServiceError, name="__lowEnergyService_error")
    def __lowEnergyService_error(self, error: QLowEnergyService.ServiceError):
        self.error.emit(f"LowEnergyService error: {error}")

    @pyqtSlot(QLowEnergyService.ServiceState, name="__lowEnergyService_stateChanged")
    def _lowEnergyService_stateChanged(self, state: QLowEnergyService.ServiceState):
        if state == QLowEnergyService.ServiceDiscovered:
            # Setup sensor channels
            for sensor_channel in [sc.SensorChannel(f"Channel {i + 1}", units_name="pF", parent=self) for i in range(10)]:
                self._addSensorChannel(sensor_channel)

            # Setup characteristics
            self.__dataCharacteristic = self._lowEnergyService.characteristic(SS16G3V197.__DATA_CHAR_UUID)
            self.__freqCharacteristic = self._lowEnergyService.characteristic(SS16G3V197.__FREQ_CHAR_UUID)
            if not self.__dataCharacteristic.isValid():
                logging.error(f"No data characteristic {SS16G3V197.__DATA_CHAR_UUID.toString()} found for "
                              f"{self._lowEnergyService.matchUuid().toString()} on device "
                              f"{self._lowEnergyController.remoteAddress().toString()} "
                              f"({self._lowEnergyController.remoteName()}).")
            if not self.__freqCharacteristic.isValid():
                logging.error(f"No frequency characteristic {SS16G3V197.__FREQ_CHAR_UUID.toString()} found for "
                              f"{self._lowEnergyService.matchUuid().toString()} on device "
                              f"{self._lowEnergyController.remoteAddress().toString()} "
                              f"({self._lowEnergyController.remoteName()}).")

        elif state == QLowEnergyService.InvalidService:
            # Remove all sensor channels
            self._clearSensorChannels()

    # endregion
