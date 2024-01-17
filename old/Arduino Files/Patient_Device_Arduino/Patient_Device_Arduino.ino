#include <M5StickC.h>
#include "LoRa.h"

void LoRa_read() {
  if (Serial2.available()) Serial.print("from LoRa: ");
  while (Serial2.available()) {
    char c = Serial2.read();
    if (c < 0x80) Serial.write(c);
    delay(1);
  }
}

void LoRa_write(char msg[]) {
  Serial2.write(msg);
  Serial.print("to LoRa: ");
  Serial.print(msg);
  delay(500);
  LoRa_read();
}

void setup() {
  M5.begin();             //Init M5StickC.  初始化M5StickC
  M5.Lcd.setRotation(3);  //Rotate the screen.  旋转屏幕
  M5.Lcd.println("Stand-by");
  delay(10);
  Serial.begin(115200);
  if (LoRaInit() < 0) Serial.print("LoRa Error");
}

void loop() {

  // Receive LoRa message from Raspberry Pi 4
  if (Serial2.available() > 0) {
    // Read the message into a string
    String publishMsg = Serial2.readString();

    // Create a new string with the format "Sensor: <data>\r\n"
    String LoRaMsg = "Sensor: " + publishMsg + "\r\n";

    // Initialize an array to store substrings and a counter for the number of substrings
    String strs[20];
    int StringCount = 0;

    // Split the publishMsg string into substrings using the '&' separator
    while (publishMsg.length() > 0) {
      int index = publishMsg.indexOf('&');

      // If there are no '&' symbols left, store the remaining string and exit the loop
      if (index == -1)  // No '&' found
      {
        strs[StringCount++] = publishMsg;
        break;
      }
      // If '&' is found, store the substring before it and update the publishMsg string
      else {
        strs[StringCount++] = publishMsg.substring(0, index);
        publishMsg = publishMsg.substring(index + 1);
      }
    }

    int BP_VALUE = strs[1].toInt();    // BP
    int SPO2_VALUE = strs[2].toInt();  // SPO2

    // Check if BP >=150 or BP <60
    // OR
    // Check if SPO2 < 60
    if ((BP_VALUE >= 150 || BP_VALUE < 60) || SPO2_VALUE <= 88) {
      // Calculate the length of the LoRa message
      int str_len = LoRaMsg.length() + 1;

      // Convert the LoRaMsg string to a character array
      char char_array[str_len];
      LoRaMsg.toCharArray(char_array, str_len);

      //Fill the screen with black (to clear the screen).  将屏幕填充黑色(用来清屏)
      M5.lcd.fillRect(0, 20, 100, 60, BLACK);
      M5.lcd.setCursor(0, 18);
      M5.Lcd.setTextSize(2);
      M5.Lcd.println(char_array);

      // Send LoRa message to LoRa device at MQTT Broker
      LoRa_write(char_array);
      LoRa_read();
    }
  }
}
