<div style="page-break-inside: avoid;">

# SSTK-Labkit-V1 Module #
## Bluetooth LE GATT Service Reference ##

This service is intended to expose the functionality of the [StretchSense 16G3V1.97](../datasheets/SS16G3V1.97.pdf) 10-channel capacitance measurement board as a set of BLE GATT characteristics. Functionality includes configurable sampling rate, data-ready notifications, store-and-foward buffering of samples, and graceful fault handling.

- [SSTK-Labkit-V1 Module](#sstk-labkit-v1-module)
  - [Bluetooth LE GATT Service Reference](#bluetooth-le-gatt-service-reference)
  - [Service Overview](#service-overview)
    - [Characteristic Table](#characteristic-table)
  - [Characteristic Details](#characteristic-details)
    - [Sensor Data](#sensor-data)
    - [Buffer Length](#buffer-length)
    - [Sampling Rate](#sampling-rate)
    - [System Fault](#system-fault)
    - [System Time](#system-time)
  - [Implementation Notes](#implementation-notes)
    - [Sample](#sample)
    - [Frame](#frame)
    - [Timestamp](#timestamp)
    - [Frame Buffer](#frame-buffer)

</div>

<div style="page-break-inside: avoid;">

## Service Overview ##
Service UUID (128-bit): `90effff0-ea02-11e9-81b4-2a2ae2dbcce4` <br>
Service Name: `SSTK-Labkit-V1`

### Characteristic Table ###
| Name            | UUID (16-bit/128-bit)                           | Format    | Properties          | Description                                                                                  |
| :-------------- | :---------------------------------------------- | :-------- | :------------------ | :------------------------------------------------------------------------------------------- |
| Sensor Data     | `fff1` / `90effff1-ea02-11e9-81b4-2a2ae2dbcce4` | 488 bytes | Read                | Returns and removes one [frame](#frame) from the top of the [frame buffer](#frame-buffer).   |
| Buffer Length   | `fff2` / `90effff2-ea02-11e9-81b4-2a2ae2dbcce4` | 2 bytes   | Read/Notify         | Returns the number of [frames](#frame) stored in the device's [frame buffer](#frame-buffer). |
| Sampling Rate   | `fff3` / `90effff3-ea02-11e9-81b4-2a2ae2dbcce4` | 1 byte    | Read/Write          | Gets/sets the sampling rate of the 16G3V1.97 device.                                         |
| System Fault    | `fff4` / `90effff4-ea02-11e9-81b4-2a2ae2dbcce4` | 1 byte    | Read/Write/Indicate | Gets/clears the current system fault status.                                                 |
| System Time     | `fff5` / `90effff5-ea02-11e9-81b4-2a2ae2dbcce4` | 8 bytes   | Read/Write          | Gets/sets the current 64-bit system time.                                                    |

</div>

<div style="page-break-inside: avoid;">

## Characteristic Details ##

### Sensor Data ###
UUID (16-bit/128-bit): `fff1` / `90effff1-ea02-11e9-81b4-2a2ae2dbcce4` <br>
Format: 488 bytes <br>
Properties: Read <br>
Default Value: `{0x00 0x00 ... 0x00}`

This read-only characteristic contains one [frame](#frame). Whenever the characteristic is read, the device transmits the oldest frame in the [frame buffer](#frame-buffer) and removes it from the buffer.

</div>

<div style="page-break-inside: avoid;">

### Buffer Length ###
UUID (16-bit/128-bit): `fff2` / `90effff2-ea02-11e9-81b4-2a2ae2dbcce4` <br>
Format: 2 bytes <br>
Properties: Read/Notify <br>
Default Value: `0x0000`

This read-only characteristic returns the number of frames currently stored in the [frame buffer](#frame-buffer). The [Sensor Data](#sensor-data) characteristic should be read this number of times to be cleared. A buffer length of `0` indicates that no data is available in the buffer to be read. Subscribing to notifications of this characteristic causes the device to notify the host any time that a new frame is added to the frame buffer.

*Note: A buffer overrun will result in a (System Fault)[#system-fault] being thrown.*

*Note: While sampling and notifications are enabled, this characteristic will notify at approximately 1/48th the [sampling rate](#sampling-rate).*

</div>

<div style="page-break-inside: avoid;">

### Sampling Rate ###
UUID (16-bit/128-bit): `fff3` / `90effff3-ea02-11e9-81b4-2a2ae2dbcce4` <br>
Format: 1 byte <br>
Properties: Read/Write <br>
Default Value `0x00` (Off)

This characteristic indicates the currently set [sampling rate](#sampling-rate) of the 16G3V1.97 device. Allowed values are listed below:

| Value  | Sampling Rate (Hz) |
| :----- | :----------------- |
| `0x01` | 25                 |
| `0x02` | 50                 |
| `0x03` | 100                |
| `0x04` | 167                |
| `0x05` | 200                |
| `0x06` | 250                |
| `0x07` | 500                |

*Note: Use of the 500 Hz sampling rate setting is not currently recommended, a memory overrun will eventually occur.*

*Note: If a value other than those listed in the preceding table is written to the characteristic, the system will throw a FAULT_INVALID_SAMP_RATE [fault](#system-fault).*

</div>

<div style="page-break-inside: avoid;">

### System Fault ###
UUID (16-bit/128-bit): `fff4` / `90effff4-ea02-11e9-81b4-2a2ae2dbcce4` <br>
Format: 1 byte <br>
Properties: Read/Write/Indicate
Default Value: `0x00` (System OK)

This characteristic is used to identify any faults incurred by the system during sample collection. If any of these faults occur, the system will cease data collection and set the appropriate flag on this characteristic. Subscribing on indications of this characteristic causes the device to indicate the fault to the host any time a fault occurs. Faults can be cleared by writing a value of `0x00` (System OK) to the characteristic. Possible fault values and causes are listed below:

| Value  | Fault Name              | Description                                                                   |
| :----- | :---------------------- | :---------------------------------------------------------------------------- |
| `0x00` | FAULT_OK                | No fault. System operating normally.                                          |
| `0x01` | FAULT_NOT_ENOUGH_MEMORY | Memory could not be allocated for some system critical task (internal error). |
| `0x02` | FAULT_FRAME_BUFF_FULL   | System frame buffer overfilled (frames not read from buffer quickly enough).  |
| `0x03` | FAULT_SAMP_BUFF_FULL    | System sample buffer full (internal error).                                   |
| `0x04` | FAULT_INVALID_SAMP_RATE | An invalid sampling rate value was selected.                                  |
| `0x05` | FAULT_MISSED_SAMPLE     | A sample from the SS16G3V1.97 was missed or skipped (internal error).         |

</div>

<div style="page-break-inside: avoid;">

### System Time ###
UUID (16-bit/128-bit): `fff5` / `90effff5-ea02-11e9-81b4-2a2ae2dbcce4` <br>
Format: 8 bytes <br>
Properties: Read/Write

This characteristics gets/sets the current system time as a 64-bit [timestamp](#timestamp).

</div>


<div style="page-break-inside: avoid;">

## Implementation Notes ##

### Sample ###
A sample refers to a set of 5 capacitance values collected at the same point in time as collected by the 16G3V1.97. These values are represented as an array of 5 2-byte, unsigned values. Each 16-bit value represents the measured capacitance in picoFarads divided by 10.

*Note: While in this context a sample refers to the capacitance values only, the 16G3V1.97 also transmits these values with a count-up sample number and status register value. This extraneous information is not included with each sample when included in a frame.*

</div>

<div style="page-break-inside: avoid;">

### Frame ###
A frame refers to a set of 48 [samples](#sample) preceded by an 8-byte [timestamp](#timestamp) value (for total of 488 bytes). The timestamp value indicates the time at which the first sample in the frame was measured. The remaining samples' times can be calculated by adding the product of the sample number and the sampling period to the timestamp:

$$
SampleTime(n) = Timestamp + n(Sampling Period)
$$

The byte-wise structure of a frame is detailed below (T = Timestamp, S#.C = Sample Number (#) at Channel (C)):
| Offset | +0        | +1        | +2        | +3        | +4        | +5        | +6        | +7        |
| :----- | :-------  | :-------  | :-------  | :-------  | :-------  | :-------  | :-------  | :-------  |
| 0      | T: 0 LSB  | T: 1      | T: 2      | T: 3      | T: 4      | T: 5      | T: 6      | T: 7 MSB  |
| 8      | S0.0 LSB  | S0.0 MSB  | S0.1 LSB  | S0.1 MSB  | S0.2 LSB  | S0.2 MSB  | S0.3 LSB  | S0.3 MSB  |
| 16     | S0.4 LSB  | S0.4 MSB  | S0.5 LSB  | S0.5 MSB  | S1.0 LSB  | S1.0 MSB  | S1.1 LSB  | S1.1 MSB  |
| 24     | S1.2 LSB  | S1.2 MSB  | S1.3 LSB  | S1.3 MSB  | S1.4 LSB  | S1.4 MSB  | S1.5 LSB  | S1.5 MSB  |
| ...    |           |           |           |           |           |           |           |           |
| 464    | S46.0 LSB | S46.0 MSB | S46.1 LSB | S46.1 MSB | S46.2 LSB | S46.2 MSB | S46.3 LSB | S46.3 MSB |
| 472    | S46.4 LSB | S46.4 MSB | S46.5 LSB | S46.5 MSB | S47.0 LSB | S47.0 MSB | S47.1 LSB | S47.1 MSB |
| 480    | S47.2 LSB | S47.2 MSB | S47.3 LSB | S47.3 MSB | S47.4 LSB | S47.4 MSB | S47.5 LSB | S47.5 MSB |


</div>

<div style="page-break-inside: avoid;">

### Timestamp ###

A timestamp in this implementation refers to a 64-bit signed integer indicating the number of microseconds that have passed since January 1, 1970, 00:00:00.

</div>

<div style="page-break-inside: avoid;">

### Frame Buffer ###

The frame buffer operates as a standard queue in which new [frames](#frame) are pushed to the back of the queue, and the oldest frames may be popped from the front of the queue. Maximum queue size may depend on available device RAM or other implementation details. However, if the device is unable to add a new frame to the frame buffer, the [Sampling Rate](#sampling-rate) characteristic will be set to `0x00` and a [System Fault](#system-fault) will be thrown.

</div>
