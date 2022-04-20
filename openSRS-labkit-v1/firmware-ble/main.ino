#include <Arduino.h>

#include "SSBluetooth.h"
#include "SSPeripheral.h"
#include "SSSystem.h"

void setup() {
  // Initialize serial for console debugging output
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);

  // Start SSPeripheral Code on Core 0
  DPRINT("Setting up StretchSense...");
  TaskHandle_t *ssPeripheralTask;
  xTaskCreatePinnedToCore(sspMain, "SS Peripheral", 1024, NULL, 1, ssPeripheralTask, 0);

  // Start SSBluetooth Code on Core 1
  DPRINT("Setting up BLE...");
  TaskHandle_t *ssBluetoothTask;
  xTaskCreatePinnedToCore(ssbMain, "SS Bluetooth", 4096, NULL, 1, ssBluetoothTask, 1);

  DPRINT("Setup complete.");
}

void loop() {
  // Do nothing
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  vTaskDelay(1000 / portTICK_PERIOD_MS);
}