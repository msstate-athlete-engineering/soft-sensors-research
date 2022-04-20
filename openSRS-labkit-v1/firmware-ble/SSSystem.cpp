#include "SSSystem.h"

/* System Global Variables */
CircularBuffer<Frame *, FRAME_BUFF_SIZE> sysFrameBuffer;
uint8_t sysSamplingRate = 0x00;
SystemFault sysFaultState = FAULT_OK;
int64_t sysTimeOffset = 0;

/* System Helper Functions */
uint16_t getLoopDelay() {
  switch (sysSamplingRate) {
  case 0x00:
    return 100 * 10; // OFF: 100 ms
  case 0x01:
    return 20 * 10; // 25 Hz: 20 ms
  case 0x02:
    return 10 * 10; // 50 Hz: 10 ms
  case 0x03:
    return 5 * 10; // 100 Hz: 5 ms
  case 0x04:
    return 3 * 10; // 167 Hz: 3 ms
  case 0x05:
    return 2500 * 10 / 1000; // 200 Hz: 2.5 ms
  case 0x06:
    return 2000 * 10 / 1000; // 250 Hz: 2 ms
  case 0x07:
    return 1000 * 10 / 1000; // 500 Hz: 1 ms
  case 0x08:
    return 500 * 10 / 1000; // 1000 Hz: 0.5 ms
  }
}

void setSystemFault(SystemFault fault) {
  sysSamplingRate = 0x00;
  sysFaultState = fault;
}