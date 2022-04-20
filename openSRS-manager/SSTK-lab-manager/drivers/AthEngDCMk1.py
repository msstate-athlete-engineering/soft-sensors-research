import struct
import time
from typing import List

from PyQt5.QtBluetooth import QBluetoothDeviceInfo, QLowEnergyService, QBluetoothUuid, QLowEnergyCharacteristic, \
    QLowEnergyController
from PyQt5.QtCore import QObject, pyqtSlot, QByteArray
from PyQt5.QtWidgets import QAction, QMenu

import SensorChannel as sc
import SensorServiceDriver as ssd


class AthEngDCMk1(ssd.SensorServiceDriver):
    __SS10SPI_BASE_UUID = QBluetoothUuid("90effff0-ea02-11e9-81b4-2a2ae2dbcce4")
    __SENSOR_DATA_CHAR_UUID = QBluetoothUuid("90effff1-ea02-11e9-81b4-2a2ae2dbcce4")
    __BUFF_SIZE_CHAR_UUID = QBluetoothUuid("90effff2-ea02-11e9-81b4-2a2ae2dbcce4")
    __SAMP_RATE_CHAR_UUID = QBluetoothUuid("90effff3-ea02-11e9-81b4-2a2ae2dbcce4")
    __SYS_FAULT_CHAR_UUID = QBluetoothUuid("90effff4-ea02-11e9-81b4-2a2ae2dbcce4")
    __SYS_TIME_CHAR_UUID = QBluetoothUuid("90effff5-ea02-11e9-81b4-2a2ae2dbcce4")

    __SAMP_RATE_CODES = [(0.0, b'\x00'), (25.0, b'\x01'), (50.0, b'\x02'), (100.0, b'\x03'), (125.0, b'\x05'),
                         (250.0, b'\x06')]

    @staticmethod
    def deviceClass() -> str:
        return "AthEngDCMk1"

    @staticmethod
    def driverName() -> str:
        return "AthEngDCMk1 Driver Version 0.1"

    @staticmethod
    def matchUuid() -> QBluetoothUuid:
        return AthEngDCMk1.__SS10SPI_BASE_UUID

    @staticmethod
    def supportedSamplingRates() -> List[float]:
        return [item[0] for item in AthEngDCMk1.__SAMP_RATE_CODES]

    def __init__(self, device_info: QBluetoothDeviceInfo, parent: QObject = None):
        super().__init__(device_info, parent)

        self.__sampling = False
        # Save Bluetooth device info
        self.__device_address = device_info.address()
        self.__device_name = device_info.name()
        self.__device_services = device_info.serviceUuids()

        # Create LowEnergyController
        self.__low_energy_controller = QLowEnergyController(device_info, self)
        self.__low_energy_controller.stateChanged.connect(self.__low_energy_controller_stateChanged)

        # LowEnergyService placeholder
        self.__low_energy_service = None

        # Connect Menu Signals
        self._contextMenu.triggered.connect(self._contextMenu_triggered)

    def deviceAddress(self):
        return self.__device_address.toString()

    def deviceName(self):
        return self.__device_name

    def deviceServices(self):
        return self.__device_services

    def samplingRate(self) -> float:
        # Don't query the device if driver isn't ready
        if self._driverState != ssd.DriverState.ReadyState:
            return 0.0

        # Read current sampling rate from device
        samp_rate_char = self.__low_energy_service.characteristic(type(self).__SAMP_RATE_CHAR_UUID)
        if samp_rate_char.isValid():
            samp_rate_code = samp_rate_char.value()
            samp_rate_pair = [item for item in type(self).__SAMP_RATE_CODES if item[1] == samp_rate_code][0]
            return samp_rate_pair[0]
        else:
            raise RuntimeError("Sampling rate characteristic not found.")

    def setSamplingRate(self, rate_hz: float) -> None:
        self.__sampling = rate_hz != 0.0
        # Check driver is ready
        if not self._driverState == ssd.DriverState.ReadyState:
            raise RuntimeError("Driver/device not ready to set sampling rate.")

        # Check sampling rate supported
        if rate_hz not in type(self).supportedSamplingRates():
            raise ValueError(f"Sampling rate {rate_hz} not supported by {type(self).driverName()}.")

        # Set sampling rate on device
        samp_rate_pair = [item for item in type(self).__SAMP_RATE_CODES if item[0] == rate_hz][0]
        samp_rate_char = self.__low_energy_service.characteristic(type(self).__SAMP_RATE_CHAR_UUID)
        if samp_rate_char.isValid():
            print(f"Writing {samp_rate_pair} to samp rate char.")
            self.__low_energy_service.writeCharacteristic(samp_rate_char, samp_rate_pair[1])
        else:
            raise RuntimeError("Sampling rate characteristic not found.")

    def _setSystemTime(self, sys_time: int):
        sys_time_bytes = struct.pack("<q", int(round(time.time() * 1.E6)))
        sys_time_char = self.__low_energy_service.characteristic(type(self).__SYS_TIME_CHAR_UUID)
        if sys_time_char.isValid():
            print(f"Writing {sys_time} to sys time char.")
            self.__low_energy_service.writeCharacteristic(sys_time_char, sys_time_bytes)
        else:
            raise RuntimeError("System time characteristic not found.")

    @pyqtSlot(QAction, name="_contextMenu_triggered")
    def _contextMenu_triggered(self, action: QAction):
        # Connect Action
        if action.data() == "connect":
            self.__low_energy_controller.connectToDevice()

        # Disconnect Action
        elif action.data() == "disconnect":
            self.__low_energy_controller.disconnectFromDevice()

        # Set Sampling Rate Action
        elif type(action.parent()) is QMenu and action.parent().objectName() == "sampling_menu":
            self.setSamplingRate(action.data())

    @pyqtSlot(QLowEnergyController.ControllerState, name="__low_energy_controller_stateChanged")
    def __low_energy_controller_stateChanged(self, state: QLowEnergyController.ControllerState):
        if state == QLowEnergyController.UnconnectedState:
            self._clearSensorChannels()
            self._setDriverState(ssd.DriverState.UnconnectedState)

        elif state == QLowEnergyController.ConnectingState:
            self._setDriverState(ssd.DriverState.PreparingState)

        elif state == QLowEnergyController.ConnectedState:
            self.__low_energy_controller.discoverServices()
            self._setDriverState(ssd.DriverState.PreparingState)

        elif state == QLowEnergyController.DiscoveringState:
            self._setDriverState(ssd.DriverState.PreparingState)

        elif state == QLowEnergyController.ClosingState:
            self._clearSensorChannels()
            self._setDriverState(ssd.DriverState.PreparingState)

        elif state == QLowEnergyController.DiscoveredState:
            self.__low_energy_service = \
                self.__low_energy_controller.createServiceObject(type(self).__SS10SPI_BASE_UUID, self)
            self.__low_energy_service.characteristicChanged.connect(self.__low_energy_service_characteristicChanged)
            self.__low_energy_service.characteristicRead.connect(self.__low_energy_service_characteristicRead)
            self.__low_energy_service.stateChanged.connect(self.__low_energy_service_stateChanged)
            self.__low_energy_service.discoverDetails()
            self._setDriverState(ssd.DriverState.PreparingState)

    @pyqtSlot(QLowEnergyService.ServiceState, name="__low_energy_service_stateChanged")
    def __low_energy_service_stateChanged(self, state: QLowEnergyService.ServiceState):
        if state == QLowEnergyService.InvalidService:
            self._setDriverState(ssd.DriverState.PreparingState)

        elif state == QLowEnergyService.DiscoveryRequired:
            self.__low_energy_service.discoverDetails()
            self._setDriverState(ssd.DriverState.PreparingState)

        elif state == QLowEnergyService.DiscoveringServices:
            self._setDriverState(ssd.DriverState.PreparingState)

        elif state == QLowEnergyService.ServiceDiscovered:
            # Create sensor channels
            for i in range(5):
                self._addSensorChannel(sc.SensorChannel(f"Channel {i}", "pF", parent=self))

            # Enable notifications on buffer size characteristic
            buff_size_char = self.__low_energy_service.characteristic(type(self).__BUFF_SIZE_CHAR_UUID)
            if not buff_size_char.isValid():
                raise RuntimeError("Buffer size characteristic not found.")

            buff_size_desc = buff_size_char.descriptor(QBluetoothUuid(QBluetoothUuid.ClientCharacteristicConfiguration))
            if not buff_size_desc.isValid():
                raise RuntimeError("Buffer size client configuration characteristic descriptor not found.")

            self.__low_energy_service.writeDescriptor(buff_size_desc, b'\x01\x00')

            # Set the driver as ready and sync device time
            self._setDriverState(ssd.DriverState.ReadyState)
            self._setSystemTime(int(round(time.time() * 1E6)))

    @pyqtSlot(QLowEnergyCharacteristic, QByteArray, name="__low_energy_service_characteristicChanged")
    def __low_energy_service_characteristicChanged(self, char: QLowEnergyCharacteristic, data: QByteArray):
        if char.uuid() == type(self).__BUFF_SIZE_CHAR_UUID and self.__sampling:
            buffer_size = struct.unpack("<H", data)[0]
            print(f"Buffer Size: {buffer_size}")
            sensor_data_char = self.__low_energy_service.characteristic(type(self).__SENSOR_DATA_CHAR_UUID)
            if not sensor_data_char.isValid():
                raise RuntimeError("Sensor data characteristic not found.")
            for _ in range(buffer_size):  # This may be the problem?
                self.__low_energy_service.readCharacteristic(sensor_data_char)

    @pyqtSlot(QLowEnergyCharacteristic, QByteArray, name="__low_energy_service_characteristicRead")
    def __low_energy_service_characteristicRead(self, char: QLowEnergyCharacteristic, value: QByteArray):
        if char.uuid() == type(self).__SENSOR_DATA_CHAR_UUID and self.__sampling:
            epoch_us = struct.unpack("<q", value[:8])[0]
            if epoch_us == 0:  # throw out zero-timestamped frames
                return

            samples = list(struct.iter_unpack("<HHHHH", value[8:]))
            channels = self.sensorChannels()
            for i_s in range(len(samples)):
                timestamp_us = epoch_us + (1.E6 / self.samplingRate()) * i_s
                for i_c in range(len(channels)):
                    samp_value = samples[i_s][i_c] / 10.0
                    channels[i_c].add_sample(timestamp_us, samp_value)

            for s_ch in channels:
                s_ch.updatePlotDataItem()
