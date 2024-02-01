//
//  920MHz LoRa/FSK RF module ES920LR3 
//
//  MaiaR create
//

//#define VIA_GROVE // connect to LoRa UNIT via GROVE

#include <M5Stack.h>
#ifdef VIA_GROVE
#define RX_pin 22 // LoRa UNIT via GROVE
#define TX_pin 21 // LoRa UNIT via GROVE
#else
#define RX_pin 16 // stack LoRa MODULE
#define TX_pin 17 // stack LoRa MODULE
#define RESET_pin 13 // stack LoRa MODULE
#define BOOT_pin 22 // stack LoRa MODULE
#endif

#include "LoRa.h"

#ifdef RESET_pin
void LoRaReset(){
  pinMode(BOOT_pin, OUTPUT); // BOOT "L"
  digitalWrite(BOOT_pin, LOW);
  pinMode(RESET_pin, OUTPUT); // NRST "L"
  digitalWrite(RESET_pin, LOW);
  delay(10);
  pinMode(RESET_pin, INPUT);  // NRST open
}
#else
void LoRaReset(){
  pinMode(RX_pin, OUTPUT);
  pinMode(TX_pin, OUTPUT);
  digitalWrite(RX_pin, LOW);
  digitalWrite(TX_pin, LOW);
  delay(1000);
  pinMode(RX_pin, INPUT);
  pinMode(TX_pin, INPUT);
}
#endif

void LoRaConfigMode(){
  String rx;
  Serial.begin(115200);
  while(1){
    LoRaReset();
    Serial2.begin(115200, SERIAL_8N1, RX_pin, TX_pin);
    Serial2.setTimeout(50);
    delay(50);
    rx = Serial2.readString();
    Serial.println(rx);
    if (rx.indexOf("Select Mode [") >= 0) break;
    LoRaCommand("config");
    delay(100); 
  }
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

int LoRaSendData(String s){
  if (LoRaCommand(s) < 0) return(-1);
  return(0);
}

String LoRaRead(){
  String rxs = Serial2.readString();
  Serial.print(rxs);

  return rxs;
}

int LoRaInit(){
  LoRaConfigMode();
  if (LoRaCommand("2"     ) < 0) return(-1); // processor mode
  if (LoRaCommand("x"     ) < 0) return(-1); // default
  if (LoRaCommand("o 1"   ) < 0) return(-1); // recv id
  if (LoRaCommand("c 5"   ) < 0) return(-1); // spread factor
  if (LoRaCommand("d 3"   ) < 0) return(-1); // channel
  if (LoRaCommand("e 2345") < 0) return(-1); // PAN ID
  if (LoRaCommand("f 10"  ) < 0) return(-1); // own ID
  if (LoRaCommand("ack 1" ) < 0) return(-1); // ack
  if (LoRaCommand("m 0"   ) < 0) return(-1); // retries
  if (LoRaCommand("g 0"   ) < 0) return(-1); // dstid 0
  if (LoRaCommand("z"     ) < 0) return(-1); // start
  return(0);
}
