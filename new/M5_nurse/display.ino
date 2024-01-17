struct PatientData {
  int status = -1;
  int room = -1;
  int bp;
  int sp;
};


PatientData patients[5];                  // Array to hold data for 5 patients
unsigned long lastUpdateTimes[5] = {0};   // Array to store last update times

// Function declarations
void addPatientVitals(int room, int bp, int sp, int s);
void checkPatientDataTimeouts();
int checkEmergency();
PatientData* getPatientData(int room);

void addPatientVitals(int room, int bp, int sp, int s) {
  PatientData* existingData = getPatientData(room);
  if (existingData) {
    // Patient data exists, update it
    existingData->bp = bp;
    existingData->sp = sp;
    existingData->status = s;
    // Serial.println("Patient data updated");

    lastUpdateTimes[room - 1] = millis();   // Assuming room numbers start from 1
  } else {
    for (int i = 0; i < 5; i++) {           // Find an empty slot for new patient data
      if (patients[i].room == -1) {         // Assuming INVALID_ROOM is a placeholder for empty data
        patients[i].room = room;
        patients[i].bp = bp;
        patients[i].sp = sp;
        patients[i].status = s;
        // Serial.println("Patient data added");
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


int checkEmergency() {
  for (int i = 0; i < 5; i++) {
    if (patients[i].status == 1) {
      return patients[i].room;
    }
  }
  return -1; // No patient with sValue 1 found
}

void checkPatientDataTimeouts() {
  unsigned long currentTime = millis();
  for (int i = 0; i < 5; i++) {
    if (patients[i].room != -1 && currentTime - lastUpdateTimes[i] > 10000) {  // Check for valid room and timeout
      patients[i].room = -1;
      patients[i].bp = -1;
      patients[i].sp = -1;
      patients[i].status = -1;
      lastUpdateTimes[i] = 0;  // Reset last update time
      // Serial.println("Patient data in room " + String(i + 1) + " reset due to timeout");
    }
  }
}

PatientData* getPatientData(int room) {
  for (int i = 0; i < 5; i++) {
    if (patients[i].room == room) {
      return &patients[i];  // Return a pointer to the patient data
    }
  }
  return nullptr;  // Return nullptr if patient not found
}

void display() {
  if (M5.BtnA.wasPressed()) {                                             // Show next room
    roomIndex = (roomIndex + NUMBER_OF_ROOMS - 1) % NUMBER_OF_ROOMS;
    Serial.println("Btn A pressed!");
    showDisplay();
  } else if (M5.BtnC.wasPressed()) {                                      // Show previous room
    roomIndex = (roomIndex + 1) % NUMBER_OF_ROOMS;
    Serial.println("Btn C pressed!");
    showDisplay();
  } else if (M5.BtnB.wasPressed() && emgRoom != -1) {                     // Show room with latest emergency
    Serial.println("Btn B pressed!");
    roomIndex = emgRoom -1;
    showDisplay();
  }

  // Send request every second (assuming non-blocking LoRaSendData)
  if (Serial2.available()) {
    String message = LoRaRead();

    // Extract RCVID and MSG from LoRa packet
    String RCVID = message.substring(4, 8);
    String MSG = message.substring(8);

    RCVID.trim();
    MSG.trim();

    // Check if messages are vital data
    if (MSG != NULL && validateVitalData(MSG)) {
      showDisplay();
    }
  }
}

void showDisplay() {

  int rm = -1;
  int bp = -1;
  int sp = -1;

  const PatientData* patient = getPatientData(roomIndex + 1);
  if (patient) {
    //printing for debugging purpose
    // Serial.println(patient->room);
    // Serial.println(patient->bp);
    // Serial.println(patient->sp);

    // assigning variable
    rm = patient->room;
    bp = patient->bp;
    sp = patient->sp;
  }

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
  M5.Lcd.println("Room:" + String(rm));

  // Display Heart Rate
  M5.Lcd.setCursor(0, 50);
  M5.Lcd.println("BPM:" + String(bp));

  // Display Oxygen Saturation
  M5.Lcd.setCursor(0, 100);
  M5.Lcd.println("O2:" + String(sp));

  // Display Room List
  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(0, 220);
  M5.Lcd.println("Room " + String(roomIndex + 1) + " of " + NUMBER_OF_ROOMS);

  // checkPatientDataTimeouts();

  if (checkEmergency() != -1) {
    emgRoom = checkEmergency();
    M5.Lcd.fillCircle(270, 35, 15, RED);
    M5.Lcd.setCursor(0, 200);
    M5.Lcd.setTextSize(2);
    M5.Lcd.println("EMERGENCY: Room " + String(emgRoom));
  } else {
    M5.Lcd.fillCircle(270, 35, 15, GREEN);
    M5.Lcd.setCursor(0, 200);
    M5.Lcd.setTextSize(2);
    M5.Lcd.println("");
  }
}

bool validateVitalData(const String& MSG) {   // Validating vital data broadcasted from Gateway
  if (MSG.startsWith("SOS_")) {               // Emergency message
    const String msg = MSG.substring(4);      // Retrieve messsage payload from LoRa
    deserialiseJson(msg);
    return true;
  }

  else if (MSG.startsWith("VITAL_")) {        // Vitals from patient device
    const String msg = MSG.substring(6);      // Retrieve message payload from LoRa
    deserialiseJson(msg);
    return true;
  }

  return false;                               // LoRa message do not contain vitals
}

void deserialiseJson(const String& json) {
  DynamicJsonDocument doc(64);  // Allocate memory dynamically based on expected message size

  // Deserialization of JSON
  DeserializationError error = deserializeJson(doc, json);

  const int room = doc["r"];
  const int sValue = doc["s"];
  const int bp = doc["bp"];
  const int sp = doc["sp"];

  addPatientVitals(room, bp, sp, sValue);
}