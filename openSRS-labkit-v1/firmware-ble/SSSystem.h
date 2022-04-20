#ifndef SS_SYSTEM_H
#define SS_SYSTEM_H

#include <Arduino.h>
#include <CircularBuffer.h>

#include "SSPeripheral.h"

// Set to 0 to disable debug messages
#define DEBUG 1

// Sets debug message printing based on the existance
// of the DEBUG flag
#if DEBUG
#define DPRINT(str) Serial.println(str)
#else
#define DPRINT(str)
#endif

#define SAMPLES_PER_FRAME 48
#define FRAME_BUFF_SIZE 512

/* Public Data Types */
enum SystemFault {
  FAULT_OK = 0x00,
  FAULT_NOT_ENOUGH_MEMORY = 0x01,
  FAULT_FRAME_BUFF_FULL = 0x02,
  FAULT_SAMP_BUFF_FULL = 0x03,
  FAULT_INVALID_SAMP_RATE = 0x04,
  FAULT_MISSED_SAMPLE = 0x05
};

struct Frame {
  int64_t timestamp;
  uint16_t samples[SAMPLES_PER_FRAME][SSP_NUM_CHANNELS_TRANSMIT];
};

/* System Global Variables */
extern CircularBuffer<Frame *, FRAME_BUFF_SIZE> sysFrameBuffer;
extern uint8_t sysSamplingRate;
extern SystemFault sysFaultState;
extern int64_t sysTimeOffset;

/* Helper Functions */
uint16_t getLoopDelay();
void setSystemFault(SystemFault fault);

#endif