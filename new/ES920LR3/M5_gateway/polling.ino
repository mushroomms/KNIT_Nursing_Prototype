#define RESPONSE_TIMEOUT 500 // Change this as needed

struct PatientData {
  int room = -1;
  int bp;
  int sp;
};

// Array to hold data for 5 patients
PatientData patients[5];

// Function declarations
void addPatientVitals(int room, int bp, int sp);
PatientData* getPatientData(int room);

void addPatientVitals(int room, int bp, int sp) {
  PatientData* existingData = getPatientData(room);
  if (existingData) {
    // Patient data exists, update it
    existingData->bp = bp;
    existingData->sp = sp;
    Serial.println("Patient data updated:");
  } else {
    // Find an empty slot for new patient data
    for (int i = 0; i < 5; i++) {
      if (patients[i].room == -1) {  // Assuming INVALID_ROOM is a placeholder for empty data
        patients[i].room = room;
        patients[i].bp = bp;
        patients[i].sp = sp;
        Serial.println("Patient data added:");
        return;
      }
    }
    // No empty slot found, handle the error
    Serial.println("Error: Patient array is full");
  }

  // Print patient data for debugging
  // Serial.println(room);
  // Serial.println(bp);
  // Serial.println(sp);
}

PatientData* getPatientData(int room) {
  for (int i = 0; i < 5; i++) {
    if (patients[i].room == room) {
      return &patients[i];  // Return a pointer to the patient data
    }
  }
  return nullptr;  // Return nullptr if patient not found
}

int currentID = 1;

void polling() {
  // Record request time and ID
  long requestTime = millis();
  currentID = (currentID % 5) + 1;

  // Send request with current ID
  LoRaSendData("SEND_REQUEST_" + String(currentID));

  // Loop until timeout or response received
  while (millis() - requestTime < RESPONSE_TIMEOUT) {
    // Check for LoRa messages with minimal delay
    if (Serial2.available()) {
      String message = LoRaRead();

      // Extract RCVID and MSG from LoRa packet
      String RCVID = message.substring(4, 8);
      String MSG = message.substring(8);

      RCVID.trim();
      MSG.trim();

      // Process message if valid from polling reply
      if (MSG != NULL && validateMessage(MSG, RCVID.toInt(), currentID)) {
        displaySuccess();
        break; // Exit polling loop after successful polling reply
      }
    }
  }

  // Handle timeout
  if (millis() - requestTime >= RESPONSE_TIMEOUT) {
    displayTimeout();
    int currentID = (currentID % 5) + 1; // next polling id
  }
}

// Validates a message, checking data ID, JSON integrity, and publishing if valid.
// Returns true if the message is a reply from polling. False if the data is not a reply from polling
bool validateMessage(const String& MSG, const int& receivedID, const int& expectedID) {
  // checking if message is in valid JSON format
  if (!MSG.startsWith("{") || !MSG.endsWith("}") || !MSG.indexOf(":")) {
    return false;
  }

  DynamicJsonDocument doc(64);  // Allocate memory dynamically based on expected message size

  // Deserialization of JSON
  DeserializationError error = deserializeJson(doc, MSG);
  if (error) {
    Serial.println(F("JSON deserialization failed: "));
    Serial.println(error.f_str());
    return false;
  }

  // Check for required keys and handle emergency status
  if (doc.containsKey("bp") && doc.containsKey("sp")) {     // Valid data from patient device
    int room = doc["r"];
    int sValue = doc["s"];
    int bp = doc["bp"];
    int sp = doc["sp"];

    String topic = "room_" + String(room);                  // topic published will be based on room number

    if (sValue == 1) {                                      // Emergency as status == 1
      Serial.println(F("[!] Emergency!!!"));
      LoRaSendData("SOS_" + String(MSG));                   // Broadcast to all nurse

      if (receivedID == expectedID) {                       // Detected emergency while polling. Polling reply
        publish((char*)topic.c_str(), (char*)MSG.c_str());  // Publish to MQTT broker
        addPatientVitals(room, bp, sp);                     // Update data for the relevant patient
        return true;
      } else {                                              // Generic emergency packet from patient. Not a polling reply
        return false;
      }
    } else if (sValue == 0 && receivedID == expectedID) {   // Non-emergency & polling reply
      publish((char*)topic.c_str(), (char*)MSG.c_str());    // Publish to MQTT broker
      LoRaSendData("VITAL_" + String(MSG));                 // Broadcast to all nurse
      return true;
    }
  }

  // Invalid data
  Serial.println(F("Not from patient device"));
  return false;
}

// // if request vitals from nurse device
// bool validateNurseDevice(const String& MSG, const int& RCVID) {

//   // setting default values to NULL
//   int bp = -1;
//   int sp = -1;

//   // if nurse device reuqests for vitals
//   if (MSG.startsWith("VITAL_REQUEST_")) {
//     const int room = MSG.substring(14).toInt();

//     const PatientData* patient = getPatientData(room);
//     if (patient) {
//       // printing for debugging purpose
//       // Serial.println(patient->room);
//       // Serial.println(patient->bp);
//       // Serial.println(patient->sp);

//       // assigning variable
//       bp = patient->bp;
//       sp = patient->sp;

//       DynamicJsonDocument doc(64);
//       doc["r"] = room;          // room number
//       doc["bp"] = bp;           // Heart rate
//       doc["sp"] = sp;           // SP02

//       String nurseRe;
//       serializeJson(doc, nurseRe);

//       // return to nurse device
//       LoRaSendData("VITALRE_" + String(RCVID) + "_" + String(nurseRe));
//       return true;
//     } else {
//       // Handle missing patient data (e.g., log error or send a notification)
//       Serial.println("No data available");
//     }
//   }

//   // Log failed validation for debugging
//   Serial.println("Failed to validate nurse device");
//   return false;
// }

String serialiseVitals(const String& room, const String& bp, const String& sp) {
  DynamicJsonDocument doc(64);
  doc["r"] = room;            // room number
  doc["bp"] = bp;             // Heart rate
  doc["sp"] = sp;             // SP02

  String json;
  serializeJson(doc, json);    // Broadcast vitals
  return json;
}

void displaySuccess() {
  M5.Lcd.setRotation(ROT);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.fillCircle(SX, SY, SR, GREEN);
}

void displayTimeout() {
  M5.Lcd.setRotation(ROT);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.fillCircle(SX, SY, SR, RED);
}