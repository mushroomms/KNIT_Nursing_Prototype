//
//  920MHz LoRa/FSK RF module ES920LR3 
//  for M5Stack
//

#include <M5Stack.h>  // for M5Stack
//#include <M5Atom.h>   // for M5Stack Atom
#include "LoRa.h"

int reset_pin = 13; // G13 for M5Stck
//int reset_pin = 23; // G23 for M5Stck Atom

void LoRaInit(){
  Serial2.setTimeout(50);
  Serial2.begin(115200, SERIAL_8N1, 16, 17); // RX:16  TX:17  for M5Stack
//  Serial2.begin(115200, SERIAL_8N1, 22, 19); // RX:22  TX:19  for M5Stack Atom
  LoRaConfig();
}

void LoRaReset(){
  String rx;
  pinMode(reset_pin, OUTPUT); // NRST "L"
  digitalWrite(reset_pin, LOW);
  delay(10);
  pinMode(reset_pin, INPUT);  // NRST open
  delay(10);
  rx = Serial2.readString();
  Serial.print(rx);
}


int LoRaCommand(String s){
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
// IDs used for Nurse Devices: 0031

// Nurse Device Configurations
int LoRaConfig(){
  LoRaReset();
  if (LoRaCommand("2") < 0) return (-1);       // processor mode
  if (LoRaCommand("c 7") < 0) return (-1);     // spread factor
  if (LoRaCommand("d 10") < 0) return (-1);    // channel
  if (LoRaCommand("e 0001") < 0) return (-1);  // PAN ID
  if (LoRaCommand("f 0002") < 0) return (-1);  // own ID
  if (LoRaCommand("g 0003") < 0) return (-1);  // broadcast
  if (LoRaCommand("z") < 0) return (-1);       // start
  return(0);
}
