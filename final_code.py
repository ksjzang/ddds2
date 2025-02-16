#!/usr/bin/env python3
import bluetooth
import time
import subprocess
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal

class BluetoothWorker(QThread):
    update_signal = pyqtSignal(str)  # UI를 업데이트하기 위한 시그널

    def run(self):
        mac = '08:D1:F9:26:65:D2'
        port = 1
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

        # 블루투스 연결을 성공할 때까지 반복 시도
        connected = False
        while not connected:
            try:
                self.update_signal.emit("Attempting to connect...")
                sock.connect((mac, port))
                connected = True
                self.update_signal.emit("Connected")
            except bluetooth.BluetoothError as e:
                self.update_signal.emit(f"Connection failed: {e}\nRetrying in 5 seconds...")
                time.sleep(5)

        # 데이터 수신 대기
        try:
            while True:
                data = sock.recv(1024)
                if data:
                    received_data = data.decode('utf-8').strip()
                    self.update_signal.emit(f"Received: {received_data}")

                    if received_data == '1':
                        self.update_signal.emit("Playing 1.mp3")
                        subprocess.run(["cvlc", "--play-and-exit", "/media/pi/3460-A639/final/stemon1.mp3"])
                    elif received_data == '2':
                        self.update_signal.emit("Playing 2.mp3")
                        subprocess.run(["cvlc", "--play-and-exit", "/media/pi/3460-A639/final/stemon2.mp3"])
                    elif received_data == '3':
                        self.update_signal.emit("Playing 3.mp3")
                        subprocess.run(["cvlc", "--play-and-exit", "/media/pi/3460-A639/final/stemon3.mp3"])
                    elif received_data == '4':
                        self.update_signal.emit("Playing 4.mp3")
                        subprocess.run(["cvlc", "--play-and-exit", "/media/pi/3460-A639/final/stemon4.mp3"])
        except:
            self.update_signal.emit("Disconnected")
        finally:
            sock.close()

class BluetoothApp(QWidget):
    def __init__(self):
        super().__init__()

        # PyQt5 GUI 설정
        self.setWindowTitle("Bluetooth MP3 Player")
        self.setGeometry(100, 100, 400, 200)

        # QLabel로 출력 표시
        self.label = QLabel("Waiting for Bluetooth connection...", self)
        self.label.setStyleSheet("font-size: 16px; color: blue;")

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # 블루투스 작업을 백그라운드 스레드에서 실행
        self.worker = BluetoothWorker()
        self.worker.update_signal.connect(self.update_label)
        self.worker.start()

    def update_label(self, message):
        """ QLabel에 출력 메시지를 업데이트하는 함수 """
        self.label.setText(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 앱 실행
    window = BluetoothApp()
    window.show()

    sys.exit(app.exec_())
