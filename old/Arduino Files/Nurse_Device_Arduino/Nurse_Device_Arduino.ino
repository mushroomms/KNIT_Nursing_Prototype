#include <Wire.h>
#include <M5Stack.h>
#include "LoRa.h"
#define NUMBER_OF_ROOMS 5

String roomArray[NUMBER_OF_ROOMS][5];  // Declare dimensions of 2D Array - Room Array

int TIMER_END = 30000;  // Time delay before refreshing values - 30 seconds
bool lowBatt = false;   // Indicate if low battery
int roomIndex = 0;      // Initial room index
int emgRoom = -1;       // Initial emergency room index

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

// Display settings
void showDisplay() {
  M5.Lcd.fillScreen(BLACK);

  //Display Battery Percentage
  if (getBatteryLevel() > 25) {
    M5.Lcd.setTextColor(WHITE);
  } else {
    M5.Lcd.setTextColor(RED);
  }
  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(270, 0);
  M5.Lcd.print(getBatteryLevel());
  M5.Lcd.print("%");

  // Display Room Number
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(4);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Room:" + roomArray[roomIndex][0]);

  // Display Heart Rate
  M5.Lcd.setCursor(0, 50);
  M5.Lcd.println("BP:" + roomArray[roomIndex][1]);

  // Display Oxygen Saturation
  M5.Lcd.setCursor(0, 100);
  M5.Lcd.println("O2:" + roomArray[roomIndex][2]);

  // Display Room List
  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(0, 220);
  M5.Lcd.println("Room " + String(roomIndex + 1) + " of " + NUMBER_OF_ROOMS);
}

void setup() {
  M5.begin();
  LoRaInit();  // Initialise LoRa
  Wire.begin();
  M5.Lcd.setBrightness(5);

  // Determine if battery is low
  if (getBatteryLevel() > 25) {
    lowBatt = false;
  } else {
    lowBatt = true;
  }

  M5.Speaker.begin();
  M5.Speaker.setVolume(1);

  // Default room values
  for (int i = 0; i < NUMBER_OF_ROOMS; i++) {
    roomArray[i][0] = String(i + 1);
    roomArray[i][1] = "NA";
    roomArray[i][2] = "NA";
    roomArray[i][3] = "0";
    roomArray[i][4] = "0";
  }
  showDisplay();
}

void loop() {

  M5.update();
  // Show next room
  if (M5.BtnA.wasPressed()) {
    roomIndex = (roomIndex + NUMBER_OF_ROOMS - 1) % NUMBER_OF_ROOMS;
    showDisplay();
  }
  // Show previous room
  if (M5.BtnC.wasPressed()) {
    roomIndex = (roomIndex + 1) % NUMBER_OF_ROOMS;
    showDisplay();
  }
  // Show room with latest emergency
  if (M5.BtnB.wasPressed() && emgRoom != -1) {
    roomIndex = emgRoom;
    showDisplay();
  }

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

  // Handle incoming LoRa messages
  if (Serial2.available() > 0) {

    String rxs = Serial2.readString();
    Serial.print(rxs);
    int index = rxs.indexOf(' ') + 1;
    String subscribeMsg = rxs.substring(index);

    // Initialize an array to store substrings and a counter for the number of substrings
    String strs[20];
    int StringCount = 0;

    // Split the subscribeMsg string into substrings using the '&' separator
    while (subscribeMsg.length() > 0) {
      int index = subscribeMsg.indexOf('&');

      // If there are no '&' symbols left, store the remaining string and exit the loop
      if (index == -1)  // No space found
      {
        strs[StringCount++] = subscribeMsg;
        break;
      }
      // If '&' is found, store the substring before it and update the subscribeMsg string
      else {
        strs[StringCount++] = subscribeMsg.substring(0, index);
        subscribeMsg = subscribeMsg.substring(index + 1);
      }
    }

    roomArray[strs[0].toInt() - 1][1] = strs[1];  // BP
    roomArray[strs[0].toInt() - 1][2] = strs[2];  // SPO2

    // Automatically reset BP and SPO2 values after a certain amount of time
    // Check and start timer for room if not started
    if (roomArray[strs[0].toInt() - 1][3] == "0") {
      roomArray[strs[0].toInt() - 1][3] = "1";
      roomArray[strs[0].toInt() - 1][4] = String(millis());
    } else {
      roomArray[strs[0].toInt() - 1][4] = String(millis());
    }

    Serial.println("Room: " + roomArray[roomIndex][0]);
    Serial.println("BP: " + roomArray[roomIndex][1]);
    Serial.println("O2: " + roomArray[roomIndex][2]);

    // Display LCD
    showDisplay();
    M5.Lcd.fillCircle(270, 35, 15, RED);
    M5.Lcd.setCursor(0, 200);
    M5.Lcd.setTextSize(2);
    M5.Lcd.println("EMERGENCY: Room " + strs[0]);
    M5.Speaker.beep();
    delay(100);
    M5.Speaker.mute();
    delay(400);
    M5.Lcd.fillCircle(270, 35, 15, BLACK);

    // Room with latest emergency
    emgRoom = strs[0].toInt() - 1;
  }

  // Check and reset values if the room has not received a BP and SPO2 reading for 30 seconds
  for (int i = 0; i < NUMBER_OF_ROOMS; i++) {
    if (roomArray[i][3] == "1") {
      if (millis() - roomArray[i][4].toInt() >= TIMER_END) {
        // Reset values
        roomArray[i][1] = "NA";
        roomArray[i][2] = "NA";
        roomArray[i][3] = "0";
        roomArray[i][4] = "0";
        if (roomIndex == i) {
          showDisplay();
        }
      }
    } else {
      continue;
    }
  }
}
