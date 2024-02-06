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
from paho.mqtt import client as mqtt_client

# i2c
SLAVE_ADR = 0x30        # hatのI2Cアドレスは0x30 ~ 0x33

# MQTT parameters
BROKER = '192.168.0.241'
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
            print(f"Send `{msg}` to topic `{topic}`")
            break
        else:
            print(f"Failed to send message to topic {topic}")
            msg_count += 1
            
            if msg_count > 5:
                break

CONFIGURED = 1  # LPWAN module configuration status. 1 = configured

# Configuration of LPWAN module
def lpwan_setup(iwc):
    print("Configuring LPWAN module")
    iwc.Write_920("ENWR")       # parameter writing
    iwc.Write_920("EENC")       # packet encryption enabled
    iwc.Write_920("STNN 0001")  # node ID 0001 (Gateway)
    iwc.Write_920("STGN")       # define group 
    iwc.Write_920("STNM 2")     # network tree mode
    iwc.Write_920("STRT 1")     # transmission high speed mode
    iwc.Write_920("ECIO")       # enable character encoding
    iwc.Write_920("DSAR")
    iwc.Write_920("DSAK")
    iwc.Write_920("DSWR")       # disable parameter writing

# function to send a unicast to a specific node ID
def unicast(nodeid, msg, iwc):
    cmd = 'TXDU{} {}'.format(nodeid, msg)
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

# function to send a broadcast
def broadcast(msg, iwc):
    cmd = 'TXDA{}'.format(msg)
    iwc.Write_920(cmd)          # note that paramter cmd only takes in MAX 32 characters (including whitespaces)

# polling through each patient device every 1 seconds
async def polling(iwc):
    while True:
        for device_id in range(2, 5):  # Iterate through device IDs 0002 to 0005
            device_id_str = f"{device_id:04d}"  # Format device ID with leading zeros
            await asyncio.sleep(1)  
            unicast(device_id_str, "POLL", iwc)
        
        #await asyncio.sleep(1)

# monitor incoming data from patient
async def monitorIncomingData(iwc, mqtt): 
    client.loop_start()

    while True:
        rx_data = iwc.Read_920()                    # 受信処理           
        if len(rx_data) >= 1:                       # 受信してない時は''が返り値 (長さ0)        
            print(rx_data, end='')                  # 受信データを画面表示
            
            if len(rx_data) >= 11:                          # 11は受信データのノード番号+RSSI等の長さ
                if (rx_data[2]==',' and    
                    rx_data[7]==',' and rx_data[10]==':'):
                    rxid = rx_data[3:7]                         # 子機(送信機)のIDを抽出 [sender ID]
                    payload = rx_data[11:]

                    # extracting payload data
                    parts = payload.split(":")
                    ROOM = parts[0]
                    STATUS = parts[1]
                    HR = parts[2]
                    SP = parts[3]

                    msg = json.dumps({'s': STATUS, 'r': ROOM, 'bp': HR, 'sp': SP})  # format to JSON
                    
                    # publish vitals to MQTT broker to be displayed
                    if STATUS == "1":
                        publish(client, msg, "hospital/emergency")
                    else:
                        publish(client, msg, "hospital/room_" + ROOM)

        await asyncio.sleep(0)

async def main(iwc, mqtt):
    await asyncio.gather(monitorIncomingData(iwc, mqtt), polling(iwc))

"""
async def poll_end_device(device_id, iwc, active_poll_tasks):
    polling_interval = active_poll_tasks[device_id]["polling_interval"]

    while True:
        unicast(device_id, "POLL", iwc)  # Send polling message

        # Wait for response, adjusting interval instantly
        response_received = asyncio.Future()
        asyncio.create_task(wait_for_response(device_id, response_received, iwc, active_poll_tasks))

        try:
            await asyncio.wait_for(response_received, timeout=5)
            polling_interval = 3  # Reset to frequent polling if response received
        except asyncio.CancelledError:
            # Task cancelled, likely due to active_poll_tasks update
            pass  # Proceed with the updated interval

        print(f"Polling device {device_id} every {polling_interval} seconds")

        await asyncio.sleep(polling_interval)

async def wait_for_response(device_id, response_received, iwc, active_poll_tasks):
    while True:
        rx_data = iwc.Read_920()
        if len(rx_data) >= 1:
            print(rx_data, end='')
            
            if len(rx_data) >= 11:             # 11は受信データのノード番号+RSSI等の長さ
                if (rx_data[2]==',' and
                    rx_data[7]==',' and rx_data[10]==':'):
                    rxid = rx_data[3:7]             # 子機(送信機)のIDを抽出 [sender ID]
                    payload = rx_data[11:]
                     
                    if rxid == device_id:
                        try:
                            response_received.set_result(True)  # Signal response received
                            break
                        except asyncio.InvalidStateError:
                            pass  # Ignore error if task cancelled

                    # Check if any node sent data and reset its polling interval if needed
                    if rxid in active_poll_tasks:
                        active_poll_tasks[rxid]["polling_interval"] = 3  # Reset interval for active node (access interval correctly)
                        print(f"Device {rxid} detected online, resetting poll interval")

        await asyncio.sleep(0)  # Check for response periodically

async def main(iwc):
    lock = asyncio.Lock()
    tasks = []
    active_poll_tasks = {}  # Track active polling tasks

    for device_id in ["0002", "0003"]:
        active_poll_tasks[device_id] = {"polling_interval": 3}  # Store interval information
        delay_time = random.uniform(1, 3)
        await asyncio.sleep(delay_time)

        task = asyncio.create_task(poll_end_device(device_id, iwc, active_poll_tasks))
        tasks.append(task)
        active_poll_tasks[device_id]["task"] = task  # Store task within a dictionary value

    await asyncio.gather(*tasks)
"""

# Main
if __name__ == '__main__':                       
    iwc = imw.IMWireClass(SLAVE_ADR)            # classの初期化
    client = connect_mqtt()

    rx_data = iwc.Read_920()                    # 受信処理           
    if len(rx_data) >= 1:                       # 受信してない時は''が返り値 (長さ0)        
            print(rx_data, end='')              # 受信データを画面表示
            time.sleep(2)

    if CONFIGURED == 0:
        lpwan_setup(iwc)

    try:
        while True:

            asyncio.run(main(iwc, client))

    except KeyboardInterrupt:                       # Ctrl + C End
        iwc.gpio_clean()
        print ('END')

