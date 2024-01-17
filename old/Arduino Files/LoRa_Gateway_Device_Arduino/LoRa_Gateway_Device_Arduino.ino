#include <M5Stack.h>
#include "LoRa.h"
#include <WiFi.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#define NUMBER_OF_ROOMS 5

// WiFi SSID/Password combination
const char* ssid = "XXXX";
const char* password = "XXXX";

// Add MQTT Broker IP address
const char* mqtt_server = "public.mqtthq.com";

// Initialise Wi-Fi & MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[50];
int value = 0;

// Read incoming LoRa messages
void LoRa_read() {
  if (Serial2.available()) Serial.print("from LoRa: ");
  while (Serial2.available()) {
    char c = Serial2.read();
    if (c < 0x80) Serial.write(c);
    delay(1);
  }
}

// Send LoRa messages
void LoRa_write(char msg[]) {
  Serial2.write(msg);
  Serial.print("to LoRa: ");
  Serial.print(msg);
  delay(500);
  LoRa_read();
}

// Setup WiFi connection
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  // Wait until WiFi is connected
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Connect to MQTT server
void reconnect() {
  // Loop until reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Attempt to connect
    if (client.connect("ESP8266Client")) {
      Serial.println("connected");

      // Subscribe to topics
      for (int i = 0; i < NUMBER_OF_ROOMS; i++) {
        String stRoom = "STRoom" + String(i + 1);
        client.subscribe((char*)stRoom.c_str());
      }
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// Handle subscribed MQTT topics
void callback(char* topic, byte* message, unsigned int length) {

  Serial.print("Subscribed Topic: ");
  Serial.print(topic);
  Serial.print(" - Message: ");
  String messageTemp;

  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println();

  // Check if the topic matches room number
  for (int i = 0; i < NUMBER_OF_ROOMS; i++) {
    if (String(topic) == "STRoom" + String(i + 1)) {

      String LoRaMsg = messageTemp + "\r\n";
      int str_len = LoRaMsg.length() + 1;
      char char_array[str_len];
      LoRaMsg.toCharArray(char_array, str_len);
      // Write the message to the LoRa device
      LoRa_write(char_array);
      LoRa_read();
    } else {
      continue;
    }
  }
}

void setup() {
  M5.begin();
  LoRaInit();  // Initialise LoRa communication

  // Default display settings
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextSize(4);
  M5.Lcd.setCursor(0, 20);
  M5.Lcd.println("ENV Display");
  M5.Lcd.println("Stand-by");
  M5.Speaker.setVolume(1);
  M5.Speaker.begin();

  // Start WiFi & MQTT connection
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}



void loop() {
  M5.update();

  // Clear M5 LCD screen
  if (M5.BtnA.wasPressed()) {
    M5.Lcd.setCursor(0, 0);
    M5.Lcd.fillScreen(BLACK);
  }

  // Reconnect to MQTT server if connection is lost
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Handle incoming LoRa messages
  if (Serial2.available() > 0) {

    String rxs = Serial2.readString();
    int index = rxs.indexOf(' ') + 1; // Get the index of first space
    int ampIndex = rxs.indexOf('&'); // Get the index of '&'

    // Extract the message from the incoming data by taking the substring from the index of first space to end
    String publishMsg = "Message: " + rxs.substring(index);

    // Convert the string to char array
    int str_len = publishMsg.length() + 1;
    char publishMsg_char[str_len];
    publishMsg.toCharArray(publishMsg_char, str_len);

    // Extract the room number from the incoming data by taking the substring from the index of first space to index of '&'
    String roomNum = rxs.substring(index, ampIndex);
    
    // Publish message to topic 'STRoom' + room number
    String pubTopic = "STRoom" + roomNum;
    client.publish((char*)pubTopic.c_str(), publishMsg_char);

    // M5 LCD display settings
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.fillCircle(270, 35, 15, RED);
    M5.Lcd.setTextColor(WHITE);
    M5.Lcd.setTextSize(2);
    M5.Lcd.setCursor(0, 20);
    M5.Lcd.println("Sensor:" + rxs.substring(index));
    M5.Speaker.beep();
    delay(100);
    M5.Speaker.mute();
    delay(400);
    M5.Lcd.fillCircle(270, 35, 15, BLACK);
  }
}
