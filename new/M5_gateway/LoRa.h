//
//  920MHz LoRa/FSK RF module ES920LR2/3 
//  for M5Stack
//

#ifndef LoRa_h
#define LoRa_h

int LoRaInit();
void LoRaConfigMode();
int LoRaCommand(String s);
int LoRaSendData(String s);
String LoRaRead();

#endif
