# -*- coding: utf-8 -*-

"""
raspihat_TXsample001.py : im_wireless.pyを使用し、受信データを出力かつテキスト保存
                          子機へACKを返す
                          Crlt+Cでプログラムを終了する
(C)2019 interplan Corp.

Ver. 0.010    2019/07/08   test version

本ソフトウェアは無保証です。
本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
改変・流用はご自由にどうぞ。
"""

import im_wireless as imw
import random
import time
import ssl
import asyncio
import json
import pymongo
from pymongo import MongoClient
from paho.mqtt import client as mqtt_client

# i2c
SLAVE_ADR = 0x30        # hatのI2Cアドレスは0x30 ~ 0x33

# MQTT parameters
BROKER = '192.168.0.240'
PORT = 8884
CLIENT_ID = f'python-mqtt-{random.randint(0, 1000)}'
USERNAME = 'username'
PASSWORD = 'password'
CA_CRT = "./certs/ca.crt"
CLIENT_CERT = "./certs/client.crt"
CLIENT_KEY = "./certs/client.key"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(self, client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #self.subscribe("hospital/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

# function to connect to MQTT broker
def connect_mqtt():
    # Set connecting Client ID
    client = mqtt_client.Client(client_id=CLIENT_ID, transport="tcp", protocol=mqtt_client.MQTTv5)
    client.username_pw_set(username=USERNAME, password=PASSWORD)
    client.tls_set(ca_certs=CA_CRT, certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
    client.tls_insecure_set(True)   # Please do not use this function in production env
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    return client

# function to publish message to specified topic
def publish(client, msg, topic):
    msg_count = 1
    while True:
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"[+] Sent `{msg}` to topic: `{topic}` via MQTT")
            break
        else:
            print(f"Failed to send message to topic {topic}")
            msg_count += 1
            
            if msg_count > 5:
                break

CONFIGURED = True   # LPWAN module configuration status. 1 = configured
ENC_KEY = "" # 256bits in hex

# Configuration of LPWAN module
def lpwan_setup(iwc):
    print("Configuring LPWAN module")
    iwc.Write_920("ENWR")           # parameter writing
    iwc.Write_920("EENC")           # packet encryption enabled
    iwc.Write_920("ERKY")           # remove enc key
    iwc.Write_920("STKY" + ENC_KEY) # add enc key
    iwc.Write_920("STNN 0001")      # node ID 0001 (Gateway)
    iwc.Write_920("STGN")           # define group 
    iwc.Write_920("STNM 2")         # network multihop mode
    iwc.Write_920("STRT 1")         # transmission high speed mode
    iwc.Write_920("ECIO")           # enable character encoding
    iwc.Write_920("DSWR")           # disable parameter writing

# function to send a unicast to a specific node ID
def unicast(nodeid, msg, iwc):
    command = 'TXDU{} {}'.format(nodeid, msg)
    cmd = command[0:32]     # only 32 characters
    print("[+] Sent: " + cmd)
    while True:     # attempt to walkaround random error 121 Remote I/O error. (Not the best option)
        try:
            iwc.Write_920(cmd)  # note that paramter cmd only takes in MAX 32 characters (including whitespaces)
            break  # or return a meaningful value if applicable
        except OSError as e:
            if e.errno == 121:
                print("Remote IO error... retrying ")   # Retry until successful
                continue
            else:
                break

# function to send a broadcast
def broadcast(msg, iwc):
    command = 'TXDA{}'.format(msg)
    cmd = command[0:32]
    print(cmd)
    while True:     # attempt to walkaround random error 121 Remote I/O error. (Not the best option)
        try:
            iwc.Write_920(cmd)  # note that paramter cmd only takes in MAX 32 characters (including whitespaces)
            return None  # or return a meaningful value if applicable
        except OSError as e:
            if e.errno == 121:
                print("Remote IO error... retrying ")   # Retry until successful
                continue
            else:
                return None

# polling through each patient device every 1 seconds
async def polling(iwc, lock):
    while True:
        for device_id in range(2, 3):
            device_id_str = f"{device_id:04d}"
            async with lock:
                print("[*] Polling ID:" + device_id_str)

                # *Polling was inconsistent, therefore removed
                #unicast(device_id_str, "POLL_" + device_id_str, iwc)
                #broadcast("POLL_" + device_id_str, iwc)
        
        await asyncio.sleep(3)

# Function to extract data from received message
def parse_data(rx_data):
    if len(rx_data) >= 1:
        print(rx_data)
        if len(rx_data) >= 11:
            try:
                if (rx_data[2]==',' and
                    rx_data[7]==',' and rx_data[10]==':'):
                    rx_id = rx_data[3:7]
                    payload = rx_data[11:]
                    
                    polling = False
            
                    # check if it is polling reply
                    if payload.startswith("P"):
                        polling = True
                    
                    if payload.startswith("N") or payload.startswith("P"):
                        payload = rx_data[12:]
            
                    data_elements = payload.split(":")
                    if len(data_elements) == 4:
                        room, status, hr, sp = data_elements
                        return rx_id, room, status, hr, sp, payload, polling
                    else:
                        raise ValueError("Invalid payload format: Delimiter count mismatch")
            
            except ValueError as e:
                print(f"Error parsing data: {e}")
                return None  # Or handle the error differently based on your requirements

# Monitor incoming data from patient
async def monitorIncomingData(iwc, mqtt, lock):
    while True:
        async with lock:
            rx_data = iwc.Read_920()
            data = parse_data(rx_data)
            if data:
                rx_id, room, status, hr, sp, payload, polling = data
                # Broadcast to nurse devices 
                if polling == True:
                    broadcast("N" + payload, iwc) 
                    print("[+] Polling received")

                # Publish vitals to MQTT
                msg = json.dumps({'s': status, 'r': room, 'bp': hr, 'sp': sp})
                topic = "hospital/emergency" if status == "1" else f"hospital/room_{room}"
                publish(client, msg, topic)
                
                # Convert JSON string to dictionary
                msg_dict = json.loads(msg)

        await asyncio.sleep(0)

async def main(iwc, mqtt):
    lock = asyncio.Lock()  # Create lock within the main function
    while True:
        await asyncio.gather(
            monitorIncomingData(iwc, client, lock),
            polling(iwc, lock)
        )

# Main
if __name__ == '__main__':                       
    iwc = imw.IMWireClass(SLAVE_ADR)            # classの初期化
    client = connect_mqtt()
    client.loop_start()

    rx_data = iwc.Read_920()                    # 受信処理           
    if len(rx_data) >= 1:                       # 受信してない時は''が返り値 (長さ0)        
            print(rx_data, end='')              # 受信データを画面表示
            time.sleep(2)

    if CONFIGURED == False:
        lpwan_setup(iwc)

    try:
        while True:
            asyncio.run(main(iwc, client))

    except KeyboardInterrupt:                       # Ctrl + C End
        iwc.gpio_clean()
        print ('END')

