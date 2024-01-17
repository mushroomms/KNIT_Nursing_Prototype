# -*- coding: utf-8 -*
'''
  @file  gain_heartbeat_SPO2.py
  @n brief： Get heart rate and oxygen saturation
  @copyright   Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license     The MIT License (MIT)
  @author      PengKaixing(kaixing.peng@dfrobot.com)
  @version     V1.0.0
  @date        2021-03-28
  @get         from https://www.dfrobot.com
  @url         https://github.com/DFRobot/DFRobot_BloodOxygen_S
'''

import sys
import os
import time
import RPi.GPIO as GPIO
import pymongo
from pymongo import MongoClient
import random
from paho.mqtt import client as mqtt_client
import lora
import ast
import struct
import sys
import ambient

room = 1

# Init LoRa
lr = lora.LoRa()

# MQTT Codes
broker = '192.168.13.15'
port = 1883
topic = "testTopic"
# Generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'

# Mongo DB Configuration
client = MongoClient('')
db = client.data
changestream = db.changestream

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from DFRobot_BloodOxygen_S import *

'''
  ctype=1：UART
  ctype=0：IIC
'''
ctype=0

if ctype==0:
  I2C_1       = 0x01               # I2C_1 Use i2c1 interface (or i2c0 with configuring Raspberry Pi file) to drive sensor
  I2C_ADDRESS = 0x57               # I2C device address, which can be changed by changing A1 and A0, the default address is 0x77
  max30102 = DFRobot_BloodOxygen_S_i2c(I2C_1 ,I2C_ADDRESS)
else:
  max30102 = DFRobot_BloodOxygen_S_uart(9600)

  
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Start recording BP and SPO2
def setup():
  while (False == max30102.begin()):
    print("init fail!")
    time.sleep(1)
  print("start measuring...")
  max30102.sensor_start_collect()
  time.sleep(1)


# Main function to continuously get BP and SPO2 readings to store in  MongoDB Database and send LoRa message
#def loop(client):
def loop():
  max30102.get_heartbeat_SPO2()
  spo2 = max30102.SPO2  if max30102.SPO2 >= 0  else 0
  bp = max30102.heartbeat if max30102.heartbeat >= 0 else 0

  print("SPO2 is : "+str(spo2)+"%")
  print("Heart rate is : "+str(bp)+"Times/min")
  print("Valid BP: "+str(max30102.BPValid))
  print("Valid SPO2: "+str(max30102.SPO2Valid))

  document = {"bp":str(bp),"spo2":str(spo2),"room":str(room),"bpvalid":str(max30102.BPValid),"spo2valid":str(max30102.SPO2Valid)}
  msg = f"{room}&{str(bp)}&{str(spo2)}"
  
  #result = client.publish(topic,msg)
  #status = result[0]
  #if status == 0:
    #print(f"Send `{msg}` to topic `{topic}`")
  #else:
    #print(f"Failed to send message to topic {topic}")

  changestream.insert_one(document)
  lr.write(msg+"\r\n")
  time.sleep(3)

  if __name__ == "__main__":
    #client = connect_mqtt()
    #client.loop_start()
    setup()
    while True:
        loop()
