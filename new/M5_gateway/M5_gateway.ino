#include "M5_gateway.h"
#define NUMBER_OF_ROOMS 5

// ===================================================
// Main Program
// ===================================================
// This runs once when the device boots. 
void setup() {
  M5.begin();
  LoRaInit();
  wifiConnect();
  mqttConnect();
  M5.Lcd.setRotation(ROT);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(TSIZE);
  M5.Lcd.setCursor(0, 20);
  M5.Lcd.println("LoRa");
  M5.Lcd.println("Gateway");
  M5.Lcd.println("Stand-by");
}

String roomArray[NUMBER_OF_ROOMS][5];  // Declare dimensions of 2D Array - Room Array

void loop(){
  M5.update();

  // Send request to current ID and check for incoming LoRa messages.
  polling();
}

void LoRaSend(String s){
  // Check for successful transmission
  if (LoRaSendData(s) == 0) {  
    // Data sent successfully
    Serial.println("Data sent successfully!");
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.fillCircle(SX, SY, SR, GREEN);
    M5.Lcd.println("Sent");   
  } 
  delay(1);
}
