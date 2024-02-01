// MQTT Broker credentials
const char* mqtt_broker = "192.168.0.240";
const char* topic = "test";
const int mqtt_port = 8883;
const char* mqttusername = "username";
const char* mqttpassword = "password";

// Set ssl certificate
const char* root_ca =  CA_CRT;
const char* server_cert = SERVER_CERT;
const char* server_key  = SERVER_KEY;

// WiFiClient espClient;
WiFiClientSecure espClient;
PubSubClient client(espClient);

void mqttConnect() {
  //Connecting to a mqtt broker width ssl certification
  espClient.setCACert(root_ca);
  espClient.setCertificate(server_cert);  // for client verification
  espClient.setPrivateKey(server_key);    // for client verification

  // Connect to the MQTT Broker remotely
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);

  while (!client.connected()) {
    String client_id = "m5stack-client";
    client_id += String(WiFi.macAddress());
    // Print the Name and the id of the esp32 controller
    Serial.printf("The client %s connects to mosquitto mqtt broker\n", client_id.c_str());
    if (client.connect(client_id.c_str(), mqttusername, mqttpassword)) {
      Serial.println("Mosquitto mqtt broker connected");
    } else {
      Serial.print("failed with state ");
      Serial.println(client.state());
      delay(2000);
    }
  }
  // Publish
  client.publish(topic, "M5Stack Gateway Device");
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("-----------------------");
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
  Serial.print("Message: ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  Serial.println("-----------------------");
}

// publish to MQTT broker
void publish(char* topic, char* payload) {
  client.loop();

  client.publish(topic, payload);
}