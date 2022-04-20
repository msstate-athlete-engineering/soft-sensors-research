import csv
import io

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QPoint, QTimer, Qt, QByteArray
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import QWidget, QFileDialog

import LoggingDialog as ld
import SensorServiceItem as ssi
import SensorServiceItemModel as ssim

MainWindowUI, MainWindowBase = uic.loadUiType("MainWindow.ui")


class MainWindow(MainWindowBase, MainWindowUI):
    __RECORD_BUTTON_FLASH_RATE_HZ = 2.0

    def __init__(self, parent: QWidget = None):
        # uic boilerplate
        MainWindowBase.__init__(self, parent=parent)
        self.setupUi(self)

        # Initialize logging dialog
        self.__loggingDialog = ld.LoggingDialog(parent=self)
        self.actionView_Log.triggered.connect(lambda: self.__loggingDialog.show())

        # Initialize service item model
        self.__sensorServiceItemModel = ssim.SensorServiceItemModel(self)
        self.__sensorServiceItemModel.discoveringChanged.connect(self.__sensorServiceItemModel_discoveringChanged)
        self.__sensorServiceItemModel.recordingChanged.connect(self.__sensorServiceItemModel_recordingChanged)
        self.sensorTreeView.setModel(self.__sensorServiceItemModel)

        # UI items event connection
        self.clearDataButton.clicked.connect(self.__clearDataButton_clicked)
        self.sensorTreeView.customContextMenuRequested.connect(self.__sensorTreeView_customContextMenuRequested)
        self.startDiscoveryButton.clicked.connect(self.__startDiscoveryButton_clicked)
        self.recordButton.clicked.connect(self.__recordButton_clicked)
        self.exportDataButton.clicked.connect(self.__exportDataButton_clicked)

        # Timer for flashing record button
        self.__recordButtonTimer = QTimer(parent=self)
        self.__recordButtonTimer.timeout.connect(self.__recordButtonTimer_timeout)
        self.__recordButtonTimer.setInterval(int(1000.0 / MainWindow.__RECORD_BUTTON_FLASH_RATE_HZ))
        self.__recordButtonTimer.start()

        # Setup plotting
        self.sensorPlotWidget.setBackground(background="w")  # White background
        self.sensorPlotWidget.setMenuEnabled(False)
        self.sensorPlotWidget.setLimits(xMin=0.0, maxXRange=5.0)
        self.sensorPlotWidget.setMouseEnabled(x=False, y=False)
        self.sensorPlotWidget.showGrid(x=True, y=True)
        self.sensorPlotWidget_legend = self.sensorPlotWidget.addLegend(offset=(-5, 5))

    def closeEvent(self, event: QCloseEvent):
        # Prevents crashing bluez on Linux
        self.__sensorServiceItemModel.stopDiscovery()
        event.accept()

    @pyqtSlot(name="__clearDataButton_clicked")
    def __clearDataButton_clicked(self):
        if not self.__sensorServiceItemModel.recording():
            self.__sensorServiceItemModel.clearRecordedData()
            self.sensorPlotWidget.clear()
            self.sensorPlotWidget_legend.scene().removeItem(self.sensorPlotWidget_legend)
            self.sensorPlotWidget_legend = self.sensorPlotWidget.addLegend(offset=(-5, 5))

    @pyqtSlot(name="__recordButton_clicked")
    def __recordButton_clicked(self):
        if self.__sensorServiceItemModel.recording():
            self.__sensorServiceItemModel.stopRecordingAllServices()
        else:
            items = self.__sensorServiceItemModel.plotDataItems()
            for i, item in enumerate(items):
                item.setPen(pg.mkPen(pg.intColor(i, hues=len(items))))
                self.sensorPlotWidget.addItem(item)
            self.__sensorServiceItemModel.startRecordingAllServices()

    @pyqtSlot(name="__recordButtonTimer_timeout")
    def __recordButtonTimer_timeout(self):
        if not self.__sensorServiceItemModel.recording():
            self.recordButton.setStyleSheet("")
            return

        if self.recordButton.styleSheet() == "":
            self.recordButton.setStyleSheet("background: rgb(255, 0, 0);")
        else:
            self.recordButton.setStyleSheet("")

    @pyqtSlot(bool, name="__sensorServiceItemModel_recordingChanged")
    def __sensorServiceItemModel_recordingChanged(self, recording: bool):
        self.clearDataButton.setEnabled(not recording)
        if not self.__sensorServiceItemModel.recording():
            self.recordButton.setIcon(QIcon.fromTheme("media-record"))  # TODO: Don't use fromTheme
            self.recordButton.setText("Record Data")
            self.sensorPlotWidget.setLimits(maxXRange=9E99)
            self.sensorPlotWidget.setMouseEnabled(x=True, y=False)
            self.exportDataButton.setEnabled(True)
        else:
            self.recordButton.setIcon(QIcon.fromTheme("media-playback-stop"))
            self.recordButton.setText("Stop Recording")
            self.sensorPlotWidget.setLimits(maxXRange=5.E6)
            self.sensorPlotWidget.setMouseEnabled(x=False, y=False)
            self.exportDataButton.setEnabled(False)

    @pyqtSlot(bool, name="__sensorServiceItemModel_discoveringChanged")
    def __sensorServiceItemModel_discoveringChanged(self, discovering: bool):
        self.startDiscoveryButton.setEnabled(not discovering)

    @pyqtSlot(QPoint, name="__sensorTreeView_customContextMenuRequested")
    def __sensorTreeView_customContextMenuRequested(self, point: QPoint):
        index = self.sensorTreeView.indexAt(point)
        if index.isValid() and isinstance(index.internalPointer(), ssi.SensorServiceItem):
            menu = index.internalPointer().contextMenu()
            if menu is not None:
                menu.exec(self.sensorTreeView.mapToGlobal(point))

    @pyqtSlot(name="__startDiscoveryButton_clicked")
    def __startDiscoveryButton_clicked(self):
        self.__sensorServiceItemModel.startDiscovery()

    @pyqtSlot(name="__exportDataButton_clicked")
    def __exportDataButton_clicked(self):
        if self.__sensorServiceItemModel.recording():
            return

        # sensor_channels = self.__sensorServiceItemModel.selectedChannels()
        # data_array = sensor_channels[0].samples["timestamp_us"]
        # for s_ch in sensor_channels:
        #     sensor_data = s_ch.samples["value"]
        #     data_array = np.vstack((data_array, sensor_data))

        sensor_channels = self.__sensorServiceItemModel.selectedChannels()
        data_series = []
        for s_ch in sensor_channels:
            data_series.append(pd.Series(data=s_ch.samples["value"], index=s_ch.samples["timestamp_us"], name=s_ch.display_name))
        data_frame = pd.DataFrame(data_series)

        # Generate CSV
        # with io.StringIO() as csv_file:
        #     csv_writer = csv.writer(csv_file)
        #     csv_writer.writerow(["Time"] + [s_ch.display_name for s_ch in sensor_channels])
        #     for data_row in data_array.T:
        #         csv_writer.writerow(data_row)
        #
        #     QFileDialog.saveFileContent(csv_file.getvalue().encode("utf-8"))

        QFileDialog.saveFileContent(data_frame.T.to_csv().encode("utf-8"))