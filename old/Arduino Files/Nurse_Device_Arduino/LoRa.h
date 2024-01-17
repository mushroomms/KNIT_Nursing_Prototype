//
//  920MHz LoRa/FSK RF module ES920LR2/3 
//  for M5Stack
//

// Include Guard
#ifndef LoRa_h
#define LoRa_h

// Initializes module and sets appropriate communication parameters
void LoRaInit();

// Sends command string to the module
// Returns integer value indicating success/failure of command
int LoRaCommand(String s);

// Sets module's configuration to default values
int LoRaConfig();

#endif
