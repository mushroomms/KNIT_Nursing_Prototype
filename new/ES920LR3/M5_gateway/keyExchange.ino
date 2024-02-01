void key_exchange() {
  uint8_t packet1[hydro_kx_XX_PACKET1BYTES];
  uint8_t packet2[hydro_kx_XX_PACKET2BYTES];
  uint8_t packet3[hydro_kx_XX_PACKET3BYTES];

  // Server static long-term key pair
  hydro_kx_keypair server_static_kp;
  hydro_kx_keygen(&server_static_kp);

  // Server process initial request from client
  hydro_kx_state st_server;
  if (Serial2.available()) {
    String packet1 = Serial2.readString();
    uint8_t packet1_bytes[packet1.length() + 1];
    packet1.getBytes(packet1_bytes, packet1.length() + 1);
    if (hydro_kx_xx_2(&st_server, packet2, packet1_bytes, NULL, &server_static_kp) != 0) {
    // abort
    }
  }
  
  LoRaSend((const char*)packet2);
  Serial.println("Packet 1:");
  Serial.println((const char*)packet1);
  Serial.println("Packet 2:");
  Serial.println((const char*)packet2);

  hydro_kx_session_keypair session_kp_server;
  if (Serial2.available()) {
    String packet3 = Serial2.readString();
    uint8_t packet3_bytes[packet3.length() + 1];
    packet3.getBytes(packet3_bytes, packet3.length() + 1);
    if (hydro_kx_xx_4(&st_server, &session_kp_server, NULL, packet3_bytes, NULL) != 0) {
      // abort
    }
  }
  // Done! session_kp.tx is the key for sending data to the client,
  // and session_kp.rx is the key for receiving data from the client.
  // The session keys are the same as those computed by the client, but swapped.
}