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
import time
import sys
import threading
from PyQt5.QtCore import QSize, Qt, QTimer, QObject, pyqtSignal, QDateTime
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPixmap, QColor

# i2c
SLAVE_ADR = 0x30        # hatのI2Cアドレスは0x30 ~ 0x33

# Function to monitor incoming data
def monitorIncomingData(iwc, data_signal):
    while True:
        try:
            rx_data = iwc.Read_920()  # 受信処理
            if rx_data:  # Check if data is received
                print(rx_data, end='')  # Display received data
                if len(rx_data) >= 11 and rx_data[2] == ',' and rx_data[7] == ',' and rx_data[10] == ':':
                    rxid = rx_data[3:7]  # Extract sender ID
                    payload = rx_data[11:]
                    if payload.startswith("N"):
                        payload = rx_data[12:]

                        data_signal.data_received.emit(payload)
        except Exception as e:
            # Handle any unexpected errors without crashing the program
            print(f"An error occurred while monitoring incoming data: {e}")

# Create a custom signal for receiving data
class DataReceivedSignal(QObject):
    data_received = pyqtSignal(str)

# Subclass QMainWindow to customize the main window
class MainWindow(QMainWindow):
    def __init__(self, iwc):
        super().__init__()
        self.iwc = iwc  # Store the IMWireClass instance

        # Initial room data
        self.rooms = {
                1: {"heart_rate": "-?-", "spo2": "-?-", "emergency": False, "last_update": QDateTime.currentDateTime(), "online": False},
                2: {"heart_rate": "-?-", "spo2": "-?-", "emergency": False, "last_update": QDateTime.currentDateTime(), "online": False},
                3: {"heart_rate": "-?-", "spo2": "-?-", "emergency": False, "last_update": QDateTime.currentDateTime(), "online": False}
        }

        self.current_room = 1
    
        self.green_circle = QLabel()
        self.room_label = QLabel("Room: -?-")
        self.hr_label = QLabel("BPM: -?-")
        self.spo2_label = QLabel("SpO2: -?-")        
        self.emergency_label = QLabel()

        self.update_room_label()
        self.update_vitals_label()
        self.update_emergency_label()

        self.init_ui()
    
    def init_ui(self):
        # Initialize UI elements
        self.setWindowTitle("Nurse Device")
        self.showFullScreen()
        self.setCursor(Qt.BlankCursor)
        self.setStyleSheet("background-color: black; color: white;")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layouts
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        top_layout = QHBoxLayout()
        data_layout = QVBoxLayout()
        emergency_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(data_layout)
        main_layout.addLayout(emergency_layout)
        main_layout.addLayout(button_layout)

        # Room info label

        self.update_room_label()
        self.room_label.setFont(QFont("Arial", 20))
        top_layout.addWidget(self.room_label)

        # Heart rate label

        self.hr_label.setFont(QFont("Arial", 20))
        data_layout.addWidget(self.hr_label)

        # SpO2 label

        self.spo2_label.setFont(QFont("Arial", 20))
        data_layout.addWidget(self.spo2_label)

        # Emergency label

        self.update_emergency_label()
        self.emergency_label.setFont(QFont("Arial", 16))
        emergency_layout.addWidget(self.emergency_label)

        # Previous button
        self.prev_button = QPushButton("<")
        self.prev_button.clicked.connect(self.previous_room)
        self.prev_button.setFont(QFont("Arial", 16))
        button_layout.addWidget(self.prev_button)

        # Next button
        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self.next_room)
        self.next_button.setFont(QFont("Arial", 16))
        button_layout.addWidget(self.next_button)

        # Green circle for indicating regularly updated room

        self.green_circle.setFixedSize(20, 20)  # Set the size of the circle
        self.green_circle.setStyleSheet("background-color: green; border-radius: 10px;")
        top_layout.addWidget(self.green_circle)
        self.green_circle.hide()

        # Start a timer to check for room data updates every 10 seconds
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_room_updates)
        self.update_timer.start(10000)  # Check for updates every 10 seconds

        # Start a thread to monitor incoming data
        self.data_signal = DataReceivedSignal()
        self.data_thread = threading.Thread(target=monitorIncomingData, args=(self.iwc, self.data_signal))
        self.data_thread.daemon = True  # Daemonize the thread so it terminates when the main thread terminates
        self.data_thread.start()

        # Connect the signal to a slot that updates the UI with received data
        self.data_signal.data_received.connect(self.update_ui_with_data)

    def update_ui_with_data(self, payload):
        try:
            # Update UI with received data
            # Example: parse rx_data and update labels accordingly
            parts = payload.split(":")
            if len(parts) == 4:
                ROOM = int(parts[0])
                STATUS = int(parts[1])
                HR = parts[2]
                SP = parts[3]

                print("Room: " + str(ROOM))
                print("BPM: " + str(HR))
                print("SPO2: " + str(SP))
                print()

                # Update room data
                self.rooms[ROOM]["heart_rate"] = HR
                self.rooms[ROOM]["spo2"] = SP
                self.rooms[ROOM]["online"] = True

                # Update emergency status
                if STATUS == 1:
                    self.rooms[ROOM]["emergency"] = True
                else:
                    self.rooms[ROOM]["emergency"] = False

                # Update the last update time for the current room
                self.rooms[self.current_room]["last_update"] = QDateTime.currentDateTime()
                self.update_vitals_label()

            else:
                print("Invalid payload format:", payload)

        except Exception as e:
            # Handle any unexpected errors without crashing the program
            print(f"An error occurred while updating UI with received data: {e}")

    def check_room_updates(self):
        # Get the current time
        current_time = QDateTime.currentDateTime()

        # Iterate through all rooms
        for room_num, room_data in self.rooms.items():
            # Check if the room's data was updated in the last 10 seconds
            last_update_time = room_data["last_update"]
            if last_update_time.msecsTo(current_time) > 10000:
                # If data hasn't been updated, hide the green circle
                if room_num == self.current_room:
                    self.green_circle.hide()
                
                # If data hasn't been updated, hide the green circle and update room data
                self.rooms[room_num]["heart_rate"] = "-?-"
                self.rooms[room_num]["spo2"] = "-?-"
                self.rooms[room_num]["emergency"] = False
                self.rooms[room_num]["online"] = False

        # Update UI after checking all rooms
        self.update_vitals_label()
        self.update_emergency_label()

    def update_vitals_label(self):
        vital_data = self.rooms.get(self.current_room, {})
    
        try:
            heart_rate = vital_data["heart_rate"]
            spo2 = vital_data["spo2"]
            online = vital_data.get("online", False)  # Default value if "online" key is not present
        
            heart_rate_color = "orange" if heart_rate == "-?-" else ("red" if not (60 < int(heart_rate) <= 150) else "white")
            spo2_color = "orange" if spo2 == "-?-" else ("red" if int(spo2) <= 88 else "white")
        
            self.hr_label.setText(f"BPM: <span style='color:{heart_rate_color}; font-weight:bold; font-size:40px;'>{heart_rate}</span>")
            self.spo2_label.setText(f"SpO2: <span style='color:{spo2_color}; font-weight:bold; font-size:40px;'>{spo2}</span>")
            
            self.update_emergency_label()

            if online:
                self.green_circle.show()
            else:
                self.green_circle.hide()
    
        except KeyError as e:
            # Handle the case when vital data keys are not found
            print(f"KeyError occurred: {e}")
        except ValueError as e:
            # Handle the case when conversion to int fails
            print(f"ValueError occurred: {e}")
        except Exception as e:
            # Handle any other unexpected errors
            print(f"An unexpected error occurred: {e}")
    
    # Update room label
    def update_room_label(self):
            self.room_label.setText(f"Room {self.current_room}")

    # Update emergency label
    def update_emergency_label(self):
        emergencies = [room for room, data in self.rooms.items() if data["emergency"]]
        if emergencies:
            emergency_text = "Emergency in rooms: " + ", ".join(map(str, emergencies))
            self.emergency_label.setText(emergency_text)
            self.emergency_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.emergency_label.clear()

    # Next room
    def next_room(self):
        self.current_room = (self.current_room % len(self.rooms)) + 1
        self.update_room_label()
        self.update_vitals_label()
        self.update_emergency_label()

    # Previous room
    def previous_room(self):
        self.current_room = self.current_room - 1 if self.current_room > 1 else len(self.rooms)
        self.update_room_label()
        self.update_vitals_label()
        self.update_emergency_label()

    # Override key press event for window
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

# Main function
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Initialize IMWireClass
    iwc = imw.IMWireClass(SLAVE_ADR)

    # Create MainWindow instance
    window = MainWindow(iwc)
    window.show()

    sys.exit(app.exec_())
