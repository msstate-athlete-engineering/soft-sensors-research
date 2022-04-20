"""Contains the SensorChannel class definition.

    SensorChannel objects are automatically created by SensorServiceDrivers when a sensor device is connected and fully
    set up by the driver.

    Examples:
    sc = SensorChannel("name", parent=mySensorServiceDriver)
    sc.add_sample(483943, 0.48502)
"""

from typing import Any, Union

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QObject

import SensorServiceItem as ssi


class SensorChannel(ssi.SensorServiceItem):
    """Represents a single sensor input channel on a device.

    SensorChannel objects are used by a SensorServiceDriver to store and format time-series sensor data in memory. This
    object is instantiated by a SensorServiceDriver upon successful initialization of a connected device. It is the
    SensorServiceDriver's responsibility to push data received from the device to this object using the add_sample or
    add_samples methods.

    Keyword Args:
        display_name: initial value for the display_name property
        units_name: initial value for hte units_name property
        disp_dec_places: initial value for the display_decimal_places property
        parent: Qt QObject parent. See PyQt5.QtCore.QObject

    Attributes:
        display_name: Human-readable text used to identify the SensorChannel to the user.
        units_name: Text abbreviation indicating the unit of measurement for data captured on the SensorChannel.
        display_decimal_places: Number of decimal places to be displayed in the user interface.
        samples: Array of timestamp-value pairs containing data captured by the sensor channel.
        latest_sample: Most recent sample received on the SensorChannel.
        plot_data_item: pyqtgraph.PlotDataItem used to interface SensorChannel data into PyQtGraph.
    """

    # region Class Initializer

    def __init__(self, display_name: str, units_name: str = "", disp_dec_places: int = 1, parent: QObject = None):
        """SensorChannel class initializer.

        See Also:
            help(SensorChannel)
        """
        # Use superclass initializer
        super(SensorChannel, self).__init__(parent)

        self.__checked_state: Qt.CheckState = Qt.Checked
        self.__display_dec_places: int = disp_dec_places
        self.__display_name: str = display_name
        self.__latest_sample: Union[float, None] = None
        self.__plot_data_item: pg.PlotDataItem = pg.PlotDataItem(name=f"{display_name} ({units_name})")
        self.__samples: Union[np.ndarray, None] = None
        self.__units_name: str = units_name

    # endregion

    # region Property Getters

    @property
    def display_name(self) -> str:
        """Human-readable text used to identify the SensorChannel to the user."""

        return self.__display_name

    @property
    def units_name(self) -> str:
        """Text abbreviation indicating the unit of measurement for data captured on the SensorChannel."""

        return self.__units_name

    @property
    def display_decimal_places(self) -> int:
        """Number of decimal places to be displayed in the user interface."""

        return self.__display_dec_places

    @property
    def samples(self) -> Union[np.ndarray, None]:
        """Array of timestamp-value pairs containing data captured by the sensor channel.

        This value is a Numpy structured ndarray with fields 'timestamp_us' (int64) and 'value' (float) containing each
        sample's collection time in microseconds since epoch and sensor value in native units, respectively.
        """

        return self.__samples

    @property
    def latest_sample(self) -> Union[float, None]:
        """Most recent sample received on the SensorChannel.

        A value of None indicates that no samples have been collected by the channel.
        """

        return self.__latest_sample

    @property
    def plot_data_item(self) -> pg.PlotDataItem:
        """pyqtgraph.PlotDataItem used to interface SensorChannel data into PyQtGraph."""
        # todo: move out of SensorChannel? or at least handle updates through SensorServiceItemModel?

        return self.__plot_data_item

    # endregion

    # region Property Setters

    @display_name.setter
    def display_name(self, display_name: str):
        """Setter for property display_name.

        See Also:
            help(display_name)
        """

        self.__display_name = display_name

    @units_name.setter
    def units_name(self, units_name: str):
        """Setter for property units_name.

        See Also:
            help(units_name)
        """

        self.__units_name = units_name

    @display_decimal_places.setter
    def display_decimal_places(self, display_decimal_places: int):
        """Setter for property display_decimal_places.

        See Also:
            help(display_decimal_places)
        """

        self.__display_dec_places = display_decimal_places

    # endregion

    # region Instance Methods

    def add_sample(self, timestamp_us: Union[int, None], value: float) -> None:
        """Processes a single sample into the SensorChannel.

        The latest_sample property is updated, and if currently recording, the sample is added to the sample array.

        Args:
            timestamp_us: the sample's collection time in microseconds since some prior epoch. If None, only the
                          latest_sample property will be updated, even if recording.
            value: the sample's numeric value
        """

        self.__latest_sample = value
        if self.recording() and timestamp_us is not None:
            new_sample = np.array([(timestamp_us, value)], dtype=[("timestamp_us", np.int64), ("value", np.float)])
            self.__samples = new_sample if self.__samples is None else np.append(self.__samples, new_sample)

    def add_samples(self):
        """todo: raises NotImplementedError"""
        raise NotImplementedError

    def clear_samples(self):
        """Removes all samples from the sample array and sets the latest_sample value to None."""

        self.__samples = None
        self.__latest_sample = None
        self.updatePlotDataItem()  # todo: remove this when plot data item stuff is figured out

    PLOT_MOVING_HIST_US = 5.0 * 1.E6  # Amount of plot history to show while recording

    def updatePlotDataItem(self):
        # todo: move this to SensorServiceItemModel on UI refresh rate

        if self.__samples is None:
            self.__plot_data_item.clear()
            return

        if self.recording():
            timestamps_us = self.__samples["timestamp_us"]
            trimmed_data = self.__samples[timestamps_us >= (timestamps_us[-1] - SensorChannel.PLOT_MOVING_HIST_US)]
        else:
            trimmed_data = self.__samples

        self.__plot_data_item.setData(x=trimmed_data["timestamp_us"], y=trimmed_data["value"])

    # endregion

    # region SensorServiceItem Implementation

    def contextMenu(self) -> None:
        __doc__ = ssi.SensorServiceItem.contextMenu.__doc__  # Inherit docstring
        return None

    def data(self, role: Qt.ItemDataRole = None) -> Any:
        __doc__ = ssi.SensorServiceItem.data.__doc__  # Inherit docstring
        if role == Qt.DisplayRole:
            if self.__latest_sample is None:
                return f"{self.__display_name}"
            return f"{self.__display_name} - {self.__latest_sample:.{self.__display_dec_places}f} {self.__units_name}"
        elif role == Qt.EditRole:
            return self.__display_name
        elif role == Qt.CheckStateRole:
            return self.__checked_state

        return None

    def flags(self) -> Qt.ItemFlags:
        __doc__ = ssi.SensorServiceItem.flags.__doc__  # Inherit docstring
        return Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def setData(self, value: Any, role: Qt.ItemDataRole = None) -> bool:
        __doc__ = ssi.SensorServiceItem.setData.__doc__  # Inherit docstring
        if role == Qt.DisplayRole or role == Qt.EditRole:
            self.__display_name = value
            self.__plot_data_item.setData(name=f"{self.__display_name} ({self.__units_name})")
        elif role == Qt.CheckStateRole:
            self.__checked_state = value
        else:
            return False

        return True

    # endregion
