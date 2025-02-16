#!/usr/bin/env python3
import bluetooth
import time
import subprocess
import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal

class BluetoothReceiver(QThread):
    """ Separate thread to continuously receive Bluetooth messages """
    message_received = pyqtSignal(str)  # Signal to send received data to the main UI

    def __init__(self, mac_address, port):
        super().__init__()
        self.mac_address = mac_address
        self.port = port
        self.sock = None
        self.running = True

    def run(self):
        """ Establish Bluetooth connection and listen for messages """
        while self.running:
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

            try:
                self.sock.connect((self.mac_address, self.port))
                print("Bluetooth Connected!")

                while self.running:
                    data = self.sock.recv(1024)
                    if data:
                        received_data = data.decode('utf-8').strip()
                        print(f"Received: {received_data}")
                        self.message_received.emit(received_data)  # Send data to main UI

            except bluetooth.BluetoothError as e:
                print(f"Connection failed: {e}\nRetrying in 5 seconds...")
                time.sleep(5)

            finally:
                if self.sock:
                    self.sock.close()

    def stop(self):
        """ Stop Bluetooth thread """
        self.running = False
        if self.sock:
            self.sock.close()

class BluetoothWorker(QThread):
    """ Main thread to handle MP3 playback """
    update_signal = pyqtSignal(str)  # Signal for UI updates
    current_process = None  # Track the currently playing VLC process

    def play_mp3(self, filename):
        """ Automatically detect USB and play MP3 from 'final/' folder """
        usb_path = self.find_usb_with_final()

        if usb_path:
            file_path = os.path.join(usb_path, filename)

            if os.path.exists(file_path):
                self.update_signal.emit(f"Playing {file_path}")

                # Stop current MP3 before playing new one
                self.stop_current_mp3()

                # **Instantly start new MP3 playback**
                self.current_process = subprocess.Popen(["cvlc", "--play-and-exit", file_path])

            else:
                self.update_signal.emit(f"File not found: {file_path}")
        else:
            self.update_signal.emit("No USB with 'final/' folder found.")

    def stop_current_mp3(self):
        """ Instantly stop the currently playing MP3 """
        if self.current_process:
            self.update_signal.emit("Stopping current MP3 playback")

            # **Forcefully kill VLC instead of waiting**
            self.current_process.kill()  
            
            # **Wait only if VLC is still running**
            if self.current_process.poll() is None:
                self.current_process.wait()  
            
            self.current_process = None  # Reset process tracker

    def find_usb_with_final(self):
        """ Find the USB drive that contains the 'final/' folder """
        base_path = "/media/pi/"
        
        # List all mounted USB devices
        usb_list = os.listdir(base_path)

        for usb in usb_list:
            usb_path = os.path.join(base_path, usb, "final")
            if os.path.exists(usb_path):  # Check if 'final/' exists
                return usb_path

        return None  # Return None if no USB contains 'final/'

    def handle_message(self, received_data):
        """ Handle received Bluetooth message and play corresponding MP3 """
        self.stop_current_mp3()  # Stop any playing MP3 before playing a new one

        if received_data == '1':
            self.update_signal.emit("Playing stemon1.mp3")
            self.play_mp3("stemon1.mp3")
        elif received_data == '2':
            self.update_signal.emit("Playing stemon2.mp3")
            self.play_mp3("stemon2.mp3")
        elif received_data == '3':
            self.update_signal.emit("Playing stemon3.mp3")
            self.play_mp3("stemon3.mp3")
        elif received_data == '4':
            self.update_signal.emit("Playing stemon4.mp3")
            self.play_mp3("stemon4.mp3")

class BluetoothApp(QWidget):
    """ PyQt5 GUI to display Bluetooth connection status """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bluetooth MP3 Player")
        self.setGeometry(100, 100, 400, 200)

        self.label = QLabel("Waiting for Bluetooth connection...", self)
        self.label.setStyleSheet("font-size: 16px; color: blue;")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Initialize Bluetooth threads
        self.worker = BluetoothWorker()
        self.receiver = BluetoothReceiver("08:D1:F9:26:65:D2", 1)

        # Connect Bluetooth receiver signal to worker
        self.receiver.message_received.connect(self.worker.handle_message)

        # Start both threads
        self.worker.start()
        self.receiver.start()

        # Connect worker signal to UI update
        self.worker.update_signal.connect(self.update_label)

    def update_label(self, message):
        """ Update QLabel with status messages """
        self.label.setText(message)

    def closeEvent(self, event):
        """ Stop Bluetooth receiver thread on application close """
        self.receiver.stop()
        self.worker.stop_current_mp3()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BluetoothApp()
    window.show()
    sys.exit(app.exec_())
