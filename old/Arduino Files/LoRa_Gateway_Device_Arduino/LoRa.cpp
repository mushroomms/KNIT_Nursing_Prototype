// Referenced from - http://ikkei.akiba.coocan.jp/ikkei_Electronics/UNIT_LR3_ENV.html
//
//  920MHz LoRa/FSK RF module ES920LR3 
//  for M5Stack
//

#include <M5Stack.h>  // for M5Stack
#include "LoRa.h"

int reset_pin = 13; // G13 for M5Stack

// Initialise serial communication with LoRa module 
void LoRaInit(){
  Serial2.setTimeout(50);
  Serial2.begin(115200, SERIAL_8N1, 16, 17); // RX:16  TX:17  for M5Stack
  LoRaConfig();
}

// Resets the LoRa module
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

// Send command to the LoRa module
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
// IDs used for Nurse Devices: 0031 - 0040

// Gateway Device Configurations
int LoRaConfig(){
  LoRaReset();
  if (LoRaCommand("2") < 0) return (-1);       // Processor Mode
  if (LoRaCommand("c 7") < 0) return (-1);     // Spread Factor
  if (LoRaCommand("d 10") < 0) return (-1);    // Channel
  if (LoRaCommand("e 0001") < 0) return (-1);  // PAN ID
  if (LoRaCommand("f 0001") < 0) return (-1);  // Own ID
  if (LoRaCommand("g 0002") < 0) return (-1);  // Destination ID
  if (LoRaCommand("l 2") < 0) return (-1);
  if (LoRaCommand("z") < 0) return (-1);       // Start
  return(0);
}
