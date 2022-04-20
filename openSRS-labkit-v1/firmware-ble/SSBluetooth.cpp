#include "SSBluetooth.h"

#include <Arduino.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

#include "SSPeripheral.h"
#include "SSSystem.h"

#define DEVICE_NAME "SSTK-Labkit-V1"
#define SERVICE_UUID "90effff0-ea02-11e9-81b4-2a2ae2dbcce4"

#define SENSOR_DATA_CHAR_UUID "90effff1-ea02-11e9-81b4-2a2ae2dbcce4"
#define BUFF_LEN_CHAR_UUID "90effff2-ea02-11e9-81b4-2a2ae2dbcce4"
#define SAMP_RATE_CHAR_UUID "90effff3-ea02-11e9-81b4-2a2ae2dbcce4"
#define SYS_FAULT_CHAR_UUID "90effff4-ea02-11e9-81b4-2a2ae2dbcce4"
#define SYS_TIME_CHAR_UUID "90effff5-ea02-11e9-81b4-2a2ae2dbcce4"

// GATT Callback Handlers
// Callbacks for Data Characteristic
class SensorDataCharCallbackHandler : public BLECharacteristicCallbacks {
  void onRead(BLECharacteristic *pChar);
};

// Callbacks for Buffer Length
class BuffLenCallbackHandler : public BLECharacteristicCallbacks {
  void onRead(BLECharacteristic *pChar);
};

// Callbacks for Sampling Rate
class SampRateCallbackHandler : public BLECharacteristicCallbacks {
  void onRead(BLECharacteristic *pChar);
  void onWrite(BLECharacteristic *pChar);
};

// Callbacks for System Faults
class SysFaultCallbackHandler : public BLECharacteristicCallbacks {
  void onRead(BLECharacteristic *pChar);
};

// Callbacks for System Time
class SysTimeCallbackHandler : public BLECharacteristicCallbacks {
  void onRead(BLECharacteristic *pChar);
  void onWrite(BLECharacteristic *pChar);
};

// Local Variables
BLEServer *bleServer;
BLEService *bleService;
BLEAdvertising *bleAdvertising;

BLECharacteristic *bleSensorDataChar;
BLECharacteristic *bleBuffLenChar;
BLECharacteristic *bleSampRateChar;
BLECharacteristic *bleSysFaultChar;
BLECharacteristic *bleSysTimeChar;

// Local Functions
void ssbSetupBluetooth();

// Primary RTOS Task Code
void ssbMain(void *params) {
  // Setup BLE and GATT API
  ssbSetupBluetooth();

  // Main event loop
  uint16_t lastSysFrameBufferSize = 0;
  SystemFault lastSysFaultState = FAULT_OK;
  while (true) {
    // Check for frame buffer size change
    uint16_t sysFrameBufferSize = sysFrameBuffer.size();
    if (sysFrameBufferSize > lastSysFrameBufferSize) {
      bleBuffLenChar->setValue(sysFrameBufferSize);
      bleBuffLenChar->notify();
    }

    // Check for any faults thrown
    else if (sysFaultState != lastSysFaultState) {
      bleSysFaultChar->setValue((uint8_t *)&sysFaultState,
                                sizeof(sysFaultState));
      bleSysFaultChar->indicate();
      DPRINT("SYSTEM FAULT: ");
      DPRINT(sysFaultState);
      lastSysFaultState = sysFaultState;
    }

    // Introduce some delay to save power
    else {
      vTaskDelay(getLoopDelay() / portTICK_PERIOD_MS);
    }
    lastSysFrameBufferSize = sysFrameBufferSize;
  }
}

void ssbSetupBluetooth() {
  // Setup BLE
  BLEDevice::init(DEVICE_NAME);
  BLEDevice::setPower(ESP_PWR_LVL_P9);
  BLEDevice::setMTU(512);
  bleServer = BLEDevice::createServer();
  bleService = bleServer->createService(SERVICE_UUID);

  // Setup Characteristics
  bleSensorDataChar = bleService->createCharacteristic(
      SENSOR_DATA_CHAR_UUID, BLECharacteristic::PROPERTY_READ);

  bleBuffLenChar = bleService->createCharacteristic(
      BUFF_LEN_CHAR_UUID,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  bleBuffLenChar->addDescriptor(new BLE2902());

  bleSampRateChar = bleService->createCharacteristic(
      SAMP_RATE_CHAR_UUID,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE);

  bleSysFaultChar = bleService->createCharacteristic(
      SYS_FAULT_CHAR_UUID, BLECharacteristic::PROPERTY_READ |
                               BLECharacteristic::PROPERTY_WRITE |
                               BLECharacteristic::PROPERTY_INDICATE);

  bleSysTimeChar = bleService->createCharacteristic(
      SYS_TIME_CHAR_UUID,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE);

  // Setup Characteristic Callbacks
  bleSensorDataChar->setCallbacks(new SensorDataCharCallbackHandler());
  bleBuffLenChar->setCallbacks(new BuffLenCallbackHandler());
  bleSampRateChar->setCallbacks(new SampRateCallbackHandler());
  bleSysFaultChar->setCallbacks(new SysFaultCallbackHandler());
  bleSysTimeChar->setCallbacks(new SysTimeCallbackHandler());

  // Start Service and Advertising
  bleService->start();
  bleAdvertising = BLEDevice::getAdvertising();
  bleAdvertising->addServiceUUID(SERVICE_UUID);
  bleAdvertising->setScanResponse(true);
  bleAdvertising->setMinPreferred(0x06); // helps with iPhone connections issue
  bleAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  DPRINT("Current MTU:");
  DPRINT(BLEDevice::getMTU());
}

// GATT Callback Handlers
// Callbacks for Data Characteristic
void SensorDataCharCallbackHandler::onRead(BLECharacteristic *pChar) {
  if (!sysFrameBuffer.isEmpty()) { // Send the next frame on the buffer
    uint8_t *nextFrame = (uint8_t *)sysFrameBuffer.shift();
    pChar->setValue(nextFrame, sizeof(Frame));
    free(nextFrame);
  } else { // If no data in buffer, send zeros
    struct Frame *emptyFrame = (Frame *)malloc(sizeof(Frame));
    memset(emptyFrame, 0, sizeof(Frame));
    pChar->setValue((uint8_t *)emptyFrame, sizeof(Frame));
    free(emptyFrame);
  }
}

// Callbacks for Buffer Length
void BuffLenCallbackHandler::onRead(BLECharacteristic *pChar) {
  uint16_t bufSize = sysFrameBuffer.size();
  pChar->setValue(bufSize);
}

// Callbacks for Sampling Rate
void SampRateCallbackHandler::onRead(BLECharacteristic *pChar) {
  pChar->setValue(&sysSamplingRate, sizeof(sysSamplingRate));
}

void SampRateCallbackHandler::onWrite(BLECharacteristic *pChar) {
  // Only allow sampling to be changed if no faults are unhandled
  if (sysFaultState == FAULT_OK) {
    uint8_t *newValue = pChar->getData();
    sysSamplingRate = *newValue;
  }
}

// Callbacks for System Fault
void SysFaultCallbackHandler::onRead(BLECharacteristic *pChar) {
  bleSysFaultChar->setValue((uint8_t *)&sysFaultState, sizeof(sysFaultState));
}

// Callbacks for System Time
void SysTimeCallbackHandler::onRead(BLECharacteristic *pChar) {
  int64_t currTime = sysTimeOffset + esp_timer_get_time();
  pChar->setValue((uint8_t *)&currTime, sizeof(currTime));
}

void SysTimeCallbackHandler::onWrite(BLECharacteristic *pChar) {
  int64_t currTime = 0;
  memcpy(&currTime, pChar->getData(), sizeof(currTime));
  sysTimeOffset = currTime - esp_timer_get_time();
}
