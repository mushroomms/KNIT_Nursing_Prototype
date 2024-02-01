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
import traceback
import sys
import time
import RPi.GPIO as GPIO
import struct
import sys
import json
import asyncio
import datetime
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

# i2c
SLAVE_ADR = 0x30        # hatのI2Cアドレスは0x30 ~ 0x33

class SharedData:
    def __init__(self):
        self.spo2 = None
        self.bp = None
        self.status = None

shared_data = SharedData()

ROOM = 1

CONFIGURED = 1  # LPWAN module configuration status. 1 = configured

# Configuration of LPWAN module
def lpwan_setup(iwc):
    print("Configuring LPWAN module")
    iwc.Write_920("ENWR")       # parameter writing
    iwc.Write_920("EENC")       # packet encryption enabled
    iwc.Write_920("STNN 0002")  # node ID 0002
    iwc.Write_920("STGN")       # join group as slave unit
    iwc.Write_920("STNM 2")     # network tree mode
    iwc.Write_920("STRT 1")     # transmission high speed mode
    iwc.Write_920("ECIO")       # enable character encoding
    iwc.Write_920("DSWR")       # disable parameter writing

# Start recording HR and SPO2
def setup():
    while (False == max30102.begin()):
        print("init fail!")
        time.sleep(5)
    print("start measuring...")
    max30102.sensor_start_collect()
    time.sleep(1)

# function to send a unicast to a specific node ID
def unicast(nodeid, msg, iwc):
    cmd = 'TXDU{} {}'.format(nodeid, msg)
    print(cmd)
    while True:     # attempt to walkaround random error 121 Remote I/O error. (Not the best option)
        try:
            iwc.Write_920(cmd)          # note that paramter cmd only takes in MAX 32 characters (including whitespaces)
            break
        except OSError as e:
            if e.errno == 121:
                print("Remote IO error... retrying ")   # Retry until successful
                continue
            else:
                break

# function to send a broadcast 
def broadcast(msg, iwc):
    cmd = 'TXDA{}'.format(msg)
    iwc.Write_920(cmd)          # note that paramter cmd only takes in MAX 32 characters (including whitespaces)

# Monitor vitals every 1s and update value
async def monitorVitals(shared_data, iwc, lock):
    while True:
        max30102.get_heartbeat_SPO2()  # getting heartrate and sp02 reading
        spo2 = max30102.SPO2 if max30102.SPO2 >= 0 else 0
        bp = max30102.heartbeat if max30102.heartbeat >= 0 else 0
        
        # Get the current date and time
        now = datetime.datetime.now()
        
        # Format the date and time using strftime()
        formatted_time = now.strftime("%d/%m/%Y %H:%M:%S")

        # Print the formatted time
        print()
        print(formatted_time)

        # Print for debugging purposes
        print(f"SPO2: {spo2}%")
        print(f"Heart rate: {bp} bpm")
        print(f"Temperature: {max30102.get_temperature_c()}°C")
        print(f"Valid BP: {max30102.BPValid}")
        print(f"Valid SPO2: {max30102.SPO2Valid}")
        print()

        # Update shared_data with new readings
        shared_data.spo2 = spo2
        shared_data.bp = bp

        # if emergency, send directly to nurse device
        if spo2 <= 88 or bp >= 150 or bp < 60:
            shared_data.status = 1              # if status 1 = emergency
            #emergency = json.dumps({'b':bp,'s':spo2,'r':ROOM}, separators=(',',':'))
            emergency = '{}:{}:{}:{}'.format(ROOM, shared_data.status, bp, spo2)    # room:status:hr:sp   
            async with lock:        # Acquire lock before I2C access
                unicast("0001", emergency, iwc)     # sending msg to gateway
        else:
            shared_data.status = 0  # if status 0 = non-emergency

        await asyncio.sleep(1)      # wait for 1 second before taking result

# monitor incoming LoRa data every 1ms
async def monitorRTS(shared_data, iwc, lock):
    while True:
        async with lock:  # Acquire lock before I2C access
            rx_data = iwc.Read_920()                    # 受信処理           
            if len(rx_data) >= 1:                       # 受信してない時は''が返り値 (長さ0)        
                print(rx_data, end='')                  # 受信データを画面表示
            
                if len(rx_data) >= 11:                          # 11は受信データのノード番号+RSSI等の長さ
                    if (rx_data[2]==',' and    
                        rx_data[7]==',' and rx_data[10]==':'):
                        rxid = rx_data[3:7]                         # 子機(送信機)のIDを抽出 [sender ID]
                        payload = rx_data[11:]
                        
                        if payload == "POLL" and rxid == "0001":    # if polling message originated from gateway
                            # Access shared data directly
                            spo2 = shared_data.spo2
                            bp = shared_data.bp
                            status = shared_data.status

                            # encode to JSON format
                            #msg = json.dumps({'s': status, 'r': ROOM, 'bp': bp, 'sp': spo2})
                            msg = '{}:{}:{}:{}'.format(ROOM, status, bp, spo2)    # room:status:hr:sp   
                            
                            print("[+] Received: ", line)
                            unicast("0001", msg, iwc)    # return vitals to gateway

        await asyncio.sleep(0.2)

# Create a lock object
lock = asyncio.Lock()

# main function which monitor vitals and RTS
async def main(iwc):
    await asyncio.gather(monitorVitals(shared_data, iwc, lock), monitorRTS(shared_data, iwc, lock))

if __name__ == "__main__":
    setup()     # setup heartrate/sp02 sensor
    iwc = imw.IMWireClass(SLAVE_ADR)    # classの初期化 
    
    rx_data = iwc.Read_920()                    # 受信処理           
    if len(rx_data) >= 1:                       # 受信してない時は''が返り値 (長さ0)        
            print(rx_data, end='')              # 受信データを画面表示
            time.sleep(1)

    if CONFIGURED == 0:
        lpwan_setup(iwc)

    try:
        asyncio.run(main(iwc))             # Start the main asynchronous function
    
    except KeyboardInterrupt:           # Ctrl + C End
        print("END\n")
   

    except Exception as error:
        print("An error occurred:", error)

    finally:                            # sensor cleanup
        max30102.sensor_end_collect()
        #iwc.gpio_clean()

        sys.stdout.flush()
