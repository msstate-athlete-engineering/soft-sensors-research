#include "SSPeripheral.h"

#include <Arduino.h>
#include <CircularBuffer.h>
#include <SPI.h>

#include "SSSystem.h"

#define SSP_INT_PIN 32
#define SSP_NSS_PIN 16

#define SAMPLE_BUF_SIZE 64

#define MOD(a, b) ((a % b) < 0 ? (a % b) + b : (a % b))

// Structure for Storing Individual Samples
struct Sample {
  uint64_t timestamp_us;
  uint16_t sensor_values[SSP_NUM_CHANNELS];
};

// Local Variables
static const SPISettings spiSettings(8000000, MSBFIRST, SPI_MODE1);
CircularBuffer<Sample *, SAMPLE_BUF_SIZE> sampleBuffer;
volatile bool newSession = true;

// Local Functions
void sspISR();
void sspSetupPeripheral();

// Primary RTOS Task Code
void sspMain(void *params) {
  // Setup SS board
  // yield();
  sspSetupPeripheral();

  // Main event loop
  uint8_t lastSamplingRate = 0x00;
  while (true) {
    // esp_task_wdt_feed();
    // Check for sampling rate change request
    if (sysSamplingRate != lastSamplingRate) {
      // Disable sensor data interrupt
      detachInterrupt(digitalPinToInterrupt(SSP_INT_PIN));

      // Check allowed sampling rate
      if (sysSamplingRate < 0x00 || sysSamplingRate > 0x08) {
        setSystemFault(FAULT_INVALID_SAMP_RATE);
      }

      // Begin SPI Transaction
      SPI.beginTransaction(spiSettings);
      digitalWrite(SSP_NSS_PIN, LOW); // Select Slave Device

      SPI.transfer(0x01);            // Config Command
      SPI.transfer(sysSamplingRate); // Output Data Rate: OFF
      SPI.transfer(0x01);            // Interrupt Mode: ON
      SPI.transfer(0x00);            // Trigger Mode: OFF
      SPI.transfer(0x0);            // Filter Mode: 1 POINT
      SPI.transfer(0x01);            // Resolution: 0.1 pF
      for (int i = 0; i < 16; i++) {
        SPI.transfer(0x00); // Zero Padding: 16 bytes
      }

      // End SPI transaction
      digitalWrite(SSP_NSS_PIN, HIGH); // De-select Slave Device
      SPI.endTransaction();

      // Clear buffers only if sampling rate changed not disabled
      // Re-enable interrupt if sampling enabled
      if (sysSamplingRate != 0x00) {
        // Free allocated frames
        for (int i = 0; i < sysFrameBuffer.size(); i++) {
          free(sysFrameBuffer[i]);
        }
        sysFrameBuffer.clear();

        // Free allocated samples
        for (int i = 0; i < sampleBuffer.size(); i++) {
          free(sampleBuffer[i]);
        }
        sampleBuffer.clear();

        newSession = true;
        attachInterrupt(digitalPinToInterrupt(SSP_INT_PIN), sspISR, FALLING);
      }

      lastSamplingRate = sysSamplingRate;
    }

    // Check for enough data to build frame
    else if (sampleBuffer.size() >= SAMPLES_PER_FRAME) {
      // Allocate memory for new Frame
      Frame *newFrame = (Frame *)malloc(sizeof(Frame));
      if (newFrame == nullptr) {
        // Fault on not enough memory
        setSystemFault(FAULT_NOT_ENOUGH_MEMORY);
        continue;
      }

      // Set new frame timestamp
      int64_t timestamp_us = sampleBuffer.first()->timestamp_us;
      newFrame->timestamp = timestamp_us + sysTimeOffset;

      // Load data into frame
      for (int i = 0; i < SAMPLES_PER_FRAME; i++) {
        Sample *nextSample = sampleBuffer.shift();
        DPRINT((uint32_t)(nextSample->timestamp_us));
        memcpy(newFrame->samples[i], nextSample->sensor_values,
               sizeof(newFrame->samples[i]));
        free(nextSample);
      }

      // Push new frame onto frame buffer
      if (!sysFrameBuffer.isFull()) {
        sysFrameBuffer.push(newFrame);
      } else {
        // Fault on full frame buffer
        setSystemFault(FAULT_FRAME_BUFF_FULL);
        continue;
      }
    }

    // Introduce some delay to save power
    else {
      // yield();
      vTaskDelay(getLoopDelay() / portTICK_PERIOD_MS);
    }
  }
}

// StretchSense Interrupt Service Routine
void sspISR() {
  noInterrupts();
  // Immediately grab timestamp
  uint64_t timestamp_us = esp_timer_get_time();

  // Allocate memory for new data
  Sample *newSample = (Sample *)malloc(sizeof(Sample));
  if (newSample == nullptr) {
    // Fault on not enough memory
    detachInterrupt(digitalPinToInterrupt(SSP_INT_PIN));
    setSystemFault(FAULT_NOT_ENOUGH_MEMORY);
    return;
  }
  newSample->timestamp_us = timestamp_us;

  // Begin SPI Transaction
  SPI.beginTransaction(spiSettings);
  digitalWrite(SSP_NSS_PIN, LOW); // Select Slave Device

  // Send command for sensor data
  SPI.transfer(0x00); // Data Command

  // Store sequence number
  int16_t seqNum = SPI.transfer(0x00); // Sequence Number

  // Read in raw capacitance values
  for (int i = 0; i < SSP_NUM_CHANNELS; i++) {
    newSample->sensor_values[i] = SPI.transfer16(0x0000);
  }

  // End SPI Transaction
  digitalWrite(SSP_NSS_PIN, HIGH); // De-select Slave Device
  SPI.endTransaction();

  // Check for expected sequence number
  static int16_t lastSeqNum;
  if (!newSession && MOD(seqNum - lastSeqNum, 256) != 1) {
    // Fault on missed sample
    detachInterrupt(digitalPinToInterrupt(SSP_INT_PIN));
    setSystemFault(FAULT_MISSED_SAMPLE);
    return;
  }
  lastSeqNum = seqNum;
  newSession = false;

  // Add new sample to buffer
  if (!sampleBuffer.isFull()) {
    sampleBuffer.push(newSample);
  } else {
    // Fault on full sample buffer
    detachInterrupt(digitalPinToInterrupt(SSP_INT_PIN));
    setSystemFault(FAULT_SAMP_BUFF_FULL);
    return;
  }
  interrupts();
}

void sspSetupPeripheral() {
  // Setup SPI and Pins
  SPI.begin();
  pinMode(SSP_INT_PIN, INPUT);
  pinMode(SSP_NSS_PIN, OUTPUT);

  // Configure StretchSense CDC
  SPI.beginTransaction(spiSettings);
  digitalWrite(SSP_NSS_PIN, LOW); // Select Slave Device

  SPI.transfer(0x01); // Config Command
  SPI.transfer(0x00); // Output Data Rate: OFF
  SPI.transfer(0x01); // Interrupt Mode: ON
  SPI.transfer(0x00); // Trigger Mode: OFF
  SPI.transfer(0x01); // Filter Mode: 1 POINT
  SPI.transfer(0x01); // Resolution: 0.1 pF
  for (int i = 0; i < 16; i++) {
    SPI.transfer(0x00); // Zero Padding: 16 bytes
  }

  // End the SPI transaction
  digitalWrite(SSP_NSS_PIN, HIGH); // De-select Slave Device
  SPI.endTransaction();
}
