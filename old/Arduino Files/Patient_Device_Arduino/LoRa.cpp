//
//  920MHz LoRa/FSK RF module ES920LR3
//  for M5Stack
//

//#define CORE  // M5Stack core
//#define KIT   // M5Stack ATOM KIT
#define HAT  // M5StickC HAT
//#define UNIT  // M5Stack GROVE Unit


#if defined(CORE)
#include <M5Stack.h>
#define RX_pin 16
#define TX_pin 17
int reset_pin = 13;

#elif defined(KIT)
#include <M5Atom.h>
#define RX_pin 22
#define TX_pin 19
int reset_pin = 23;

#elif defined(HAT)
#include <M5StickC.h>
#define RX_pin 26
#define TX_pin 0

#elif defined(UNIT)
#include <M5StickC.h>
#define RX_pin 33
#define TX_pin 32

#endif

#include "LoRa.h"

#if defined(CORE) || defined(KIT)
void LoRaReset() {
  pinMode(reset_pin, OUTPUT);  // NRST "L"
  digitalWrite(reset_pin, LOW);
  delay(10);
  pinMode(reset_pin, INPUT);  // NRST open
}
#elif defined(HAT) || defined(UNIT)
void LoRaReset() {
  pinMode(RX_pin, OUTPUT);
  pinMode(TX_pin, OUTPUT);
  digitalWrite(RX_pin, LOW);
  digitalWrite(TX_pin, LOW);
  delay(1000);
  pinMode(RX_pin, INPUT);
  pinMode(TX_pin, INPUT);
}
#endif

void LoRaConfigMode() {
  String rx;
  while (1) {
    LoRaReset();
    Serial2.setTimeout(50);
    Serial2.begin(115200, SERIAL_8N1, RX_pin, TX_pin);
    delay(50);
    rx = Serial2.readString();
    Serial.println(rx);
    if (rx.indexOf("Select Mode [") >= 0) break;
    LoRaCommand("config");
    delay(100);
  }
}


int LoRaCommand(String s) {
  String rx;
  Serial2.print(s);
  Serial2.print("\r\n");
  Serial2.flush();
  Serial.println(s);
  Serial.flush();
  delay(10);
  rx = Serial2.readString();
  Serial.print(rx);
  return (rx.indexOf("OK"));
}

// LoRa Configurations Used:
// Spread Factor: 7
// Channel: 10
// Pan ID: 0001
// ID used for Gateway device: 0001
// ID used for Raspberry Pi 4s: 0011 - 0020  
// IDs used for Sensor Devices (M5StickC): 0021 - 0030
// IDs used for Nurse Devices: 0031 - 0040

// Sensor Device Configurations
int LoRaInit() {
  LoRaConfigMode();
  if (LoRaCommand("2") < 0) return (-1);       // processor mode
  if (LoRaCommand("c 7") < 0) return (-1);     // spread factor
  if (LoRaCommand("d 10") < 0) return (-1);    // channel
  if (LoRaCommand("e 0001") < 0) return (-1);  // PAN ID
  if (LoRaCommand("f 0022") < 0) return (-1);  // own ID
  if (LoRaCommand("g 0001") < 0) return (-1);  // broadcast
  if (LoRaCommand("l 2") < 0) return (-1);
  if (LoRaCommand("z") < 0) return (-1);       // start
  return (0);
}
