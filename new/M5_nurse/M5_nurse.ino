#include "M5_nurse.h"
#define NUMBER_OF_ROOMS 5
#define ID 10

int TIMER_END = 30000;  // Time delay before refreshing values - 30 seconds
bool lowBatt = false;   // Indicate if low battery
int roomIndex = 0;      // Initial room index
int emgRoom = -1;       // Initial emergency room index

// ===================================================
// Main Program
// ===================================================
// This runs once when the device boots. 
void setup() {
  M5.begin();
  LoRaInit();
  M5.Lcd.setRotation(ROT);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(TSIZE);
  M5.Lcd.setCursor(0, 20);
  M5.Lcd.println("LoRa");
  M5.Lcd.println("Nurse");
  M5.Lcd.println("Stand-by");
}

void loop(){
  M5.update();
  display();
  checkBattery();
}

// Measure battery level - 0%, 25%, 50%, 75%, 100%
int8_t getBatteryLevel() {
  Wire.beginTransmission(0x75);
  Wire.write(0x78);
  if (Wire.endTransmission(false) == 0
      && Wire.requestFrom(0x75, 1)) {
    switch (Wire.read() & 0xF0) {
      case 0xE0: return 25;
      case 0xC0: return 50;
      case 0x80: return 75;
      case 0x00: return 100;
      default: return 0;
    }
  }
  return -1;
}

void checkBattery() {
    // Check if low battery
  if (getBatteryLevel() <= 25 && !lowBatt) {
    M5.Lcd.setTextColor(RED);
    M5.Lcd.fillRect(270, 0, 40, 15, BLACK);
    M5.Lcd.setTextSize(2);
    M5.Lcd.setCursor(270, 0);
    M5.Lcd.print(getBatteryLevel());
    M5.Lcd.print("%");
    M5.Lcd.setTextColor(WHITE);
    lowBatt = true;
  }

  // Check if battery increases over 50%
  if (getBatteryLevel() > 25 && lowBatt) {
    M5.Lcd.setTextColor(WHITE);
    M5.Lcd.fillRect(270, 0, 40, 15, BLACK);
    M5.Lcd.setTextSize(2);
    M5.Lcd.setCursor(270, 0);
    M5.Lcd.print(getBatteryLevel());
    M5.Lcd.print("%");
    lowBatt = false;
  }
}