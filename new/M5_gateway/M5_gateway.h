// ===================================================
// Put all pin mappings and library here
// ===================================================
//M5Stack 
#include <M5Stack.h>
#define ROT 1
#define TSIZE 4
#define RPOS 180
#define SX 270
#define SY 35
#define SR 15
#undef min

// Encryption
#include <AESLib.h>
/* declare a global AESLib object */
AESLib aesLib;

// Key Exchange
#include <hydrogen.h>

// LoRa
#include "LoRa.h"

// Base64 Encoding
#include <arduino_base64.hpp>

// WiFi & MQTT
#include <WiFi.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "credentials.h"

// JSON
#include <ArduinoJson.h>
