# -*- coding: utf-8 -*-

"""
im_wireless.py : IM920(c/s)をHATにて使うライブラリ
(C)2019 interplan Corp.

Ver. 0.010    2019/07/08   test version

本ソフトウェアは無保証です。
本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
改変・流用はご自由にどうぞ。
"""

import time
import smbus
import RPi.GPIO as GPIO

# ピンアサイン (BCM)
IRQ_PIN = 17            # PIC I2C割り込みピン
XMIT_PIN = 18           # 送信中出力ピン
SLEEP_PIN = 22          # スリープピン
RESET_PIN = 23          # リセットピン
BUSY_PIN = 27           # BUSYピン

RXBUF_MAXSIZE = 0x400


class IMWireClass:

    def __init__(self, sladr):                                   # 初期化
        self.rxbuf_head = 0                                         # i2c受信バッファ
        self.rxbuf_tail = 0
        self.rxbuf_num = 0
        self.rxbuf_maxsize = RXBUF_MAXSIZE
        self.i2c_rxbuf = [0] * self.rxbuf_maxsize
        #self.i2c_rxbuf =  np.zeros(self.rxbuf_maxsize, dtype='U250')         
        self.slave_adr = sladr

        GPIO.setmode(GPIO.BCM)                                      # GPIO設定
        GPIO.setup(RESET_PIN, GPIO.OUT)
        GPIO.setup(XMIT_PIN, GPIO.IN)
        GPIO.setup(SLEEP_PIN, GPIO.IN)
        GPIO.setup(IRQ_PIN, GPIO.IN)
        GPIO.setup(BUSY_PIN, GPIO.IN)

        GPIO.output(RESET_PIN, 1)
    
        self.i2c = smbus.SMBus(1)                                   # i2cの準備
        
        [self.i2c.read_byte(self.slave_adr) for i in range(300)]    # 変換ICのバッファ初期化
        
        # GPIO割り込み設定　必要に応じてXMITやSLEEPも使用
        GPIO.add_event_detect(IRQ_PIN, GPIO.RISING, callback=self.irq_intrpt, bouncetime=5)
        GPIO.add_event_detect(XMIT_PIN, GPIO.RISING, callback=self.xmit_intrpt, bouncetime=1)
        GPIO.add_event_detect(SLEEP_PIN, GPIO.RISING, callback=self.slp_intrpt, bouncetime=1)

        self.Reboot_920()
    
    def remove_interrupt(self, port):                           # GPIO割り込み削除
            GPIO.remove_event_detect(port)
    
    def Reboot_920(self):                                       # 再起動
        GPIO.output(RESET_PIN, 0)
        time.sleep(500e-3)
        GPIO.output(RESET_PIN, 1)
        time.sleep(500e-3)
    
    def Write_920(self, cmd):                                   # Moduleにコマンドを入力
        busy_sts = 0
        if not '?' == cmd[0] :                                      # コマンドの先頭がWake-up用トリガならModuleはSleep中と想定
            busy_sts = self.busy_status()
            while busy_sts:
                time.sleep(1e-3)
                busy_sts = self.busy_status()

        #print('>'+cmd)                                              # コマンドを表示
        self.i2c.write_i2c_block_data(self.slave_adr, 0, [ord(i) for i in cmd])
    
    def Read_920(self):                                         # 受信データを返す
        buf = ''                                                
        if self.rxbuf_num >= 1:                                     # 受信データ(レスポンス含む)があれば
            buf = self.i2c_rxbuf[self.rxbuf_head]                   
            self.rxbuf_head += 1
            self.rxbuf_head &= self.rxbuf_maxsize - 1
            self.rxbuf_num -= 1
        
        return buf
            
    def irq_intrpt(self, gpio):                                 # I2C割り込み
        if gpio == IRQ_PIN:
            i2c_rxlen = 0
            while i2c_rxlen == 0:                                       # 受信データ長を取得
                i2c_rxlen = self.i2c.read_byte(self.slave_adr)        

            if i2c_rxlen >= 1:                                          # データ保存処理
                buf = ''
                while i2c_rxlen >= 1:
                    buf += chr(self.i2c.read_byte(self.slave_adr))
                    i2c_rxlen -= 1
                self.i2c_rxbuf[self.rxbuf_tail] = buf                   

                self.rxbuf_tail += 1                                    # バッファの更新処理
                self.rxbuf_tail &= self.rxbuf_maxsize - 1
                self.rxbuf_num += 1
                if self.rxbuf_num > self.rxbuf_maxsize:                 # バッファを上書きしたら
                    self.rxbuf_num = self.rxbuf_maxsize 
                    self.rxbuf_head += 1                                    # headを更新
                    self.rxbuf_head &= self.rxbuf_maxsize - 1
            
    def slp_intrpt(self, gpio):                                 # SLEEP
        slp_sts = 1
    
    def xmit_intrpt(self, gpio):                                # ルート探索,ACK返送,中継でもここに来る
        xmit_sts = 1
    
    def busy_status(self):                                      # busyのHIGH/LOWを返す
        return GPIO.input(BUSY_PIN)

    def gpio_clean(self):                                       # プログラム終了時に必ず使用
        GPIO.cleanup()
