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
import time
import RPi.GPIO as GPIO
import lora
import struct
import sys
import json
import asyncio
from datetime import datetime
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


class SharedData:
    def __init__(self):
        self.spo2 = None
        self.bp = None
        self.status = None

shared_data = SharedData()

ROOM = 1

# Init LoRa
lr = lora.LoRa()

# Start recording BP and SPO2
def setup():
  while (False == max30102.begin()):
    print("init fail!")
    time.sleep(5)
  print("start measuring...")
  max30102.sensor_start_collect()
  time.sleep(1)

def printable(l):
    x = struct.unpack(str(len(l)) + 'b', l)
    y = ''
    for i in range(len(x)):
        if x[i] >= 0:
            y = y + chr(x[i])
    return y

def sendcmd(cmd):
    # print(cmd)
    lr.write(cmd)
    t = time.time()
    while (True):
        if (time.time() - t) > 5:
            print('panic: %s' % cmd)
            exit()
        line = lr.readline()
        if 'OK' in printable(line):
            # print(line)
            return True
        elif 'NG' in printable(line):
            # print(line)
            return False

# function for LoRa initialization
def setMode():
    lr.write('config\r\n')
    lr.s.flush()
    time.sleep(0.2)
    lr.reset()
    time.sleep(1.5)

    line = lr.readline()
    while not ('Mode' in printable(line)):
        line = lr.readline()
        # if len(line) > 0:
            # print(line)

    # LoRa configuration
    sendcmd('2\r\n')
    #sendcmd('bw %d\r\n' % bw)
    #sendcmd('sf %d\r\n' % sf)
    sendcmd('x\r\n')
    sendcmd('o 1\r\n')
    sendcmd('c 5\r\n')
    sendcmd('d 3\r\n')
    sendcmd('e 2345\r\n')
    sendcmd('f 1\r\n')
    sendcmd('m 0\r\n')
    sendcmd('g 0\r\n')
    sendcmd('q 2\r\n')
    sendcmd('ack 1\r\n')
    sendcmd('z\r\n')

    lr.reset()
    print('LoRa module set to new mode')
    time.sleep(1)
    sys.stdout.flush()

# function to send data
def sendLoRa(msg):
    sendcmd(msg + '\r\n')
    print('[+] Sent: ' + msg)
    print()

# Monitor vitals every 1s and update value
async def monitorVitals(shared_data):
    while True:
      max30102.get_heartbeat_SPO2()  # getting heartrate and sp02 reading
      spo2 = max30102.SPO2 if max30102.SPO2 >= 0 else 0
      bp = max30102.heartbeat if max30102.heartbeat >= 0 else 0

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
          shared_data.status = 1 # if status 1 = emergency
          emergency = json.dumps({'s': 1, 'r': ROOM, 'bp': bp, 'sp': spo2})
          print('[!] Emergency!')
          print()
          sendLoRa(emergency)
      else:
          shared_data.status = 0 # if status 0 = non-emergency

      await asyncio.sleep(1)

# monitor incoming LoRa data every 1ms
async def monitorRTS(shared_data):
    while True:
      # listening for LoRa incoming data. Timeout 1 second
      line = lr.readline(1)
      # print(line)

      # if receive send request from gateway
      if 'SEND_REQUEST_1' in printable(line): 
          # Access shared data directly
          spo2 = shared_data.spo2
          bp = shared_data.bp
          status = shared_data.status

          # encode to JSON format
          msg = json.dumps({'s': status, 'r': ROOM, 'bp': bp, 'sp': spo2})

          print("[+] Received: ", line)
          sendLoRa(msg)    # return vitals to gateway

      await asyncio.sleep(0.1)

# main function which monitor vitals and RTS
async def main():
  await asyncio.gather(monitorVitals(shared_data), monitorRTS(shared_data))

if __name__ == "__main__":
  setup()     # setup heartrate/sp02 sensor
  setMode()   # setup LoRa module

  try:
      asyncio.run(main())             # Start the main asynchronous function
  except KeyboardInterrupt:
      max30102.sensor_end_collect()   # Ensure sensor cleanup
      sys.exit()

  sys.stdout.flush()