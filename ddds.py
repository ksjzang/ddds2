#!/usr/bin/env python3
import bluetooth
import time
import subprocess
import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal

class BluetoothWorker(QThread):
    update_signal = pyqtSignal(str)  # UI를 업데이트하기 위한 시그널
    current_process = None  # 현재 실행 중인 VLC 프로세스 추적

    def run(self):
        mac = '08:D1:F9:26:65:D2'  # ESP32 Bluetooth MAC 주소
        port = 1

        while True:
            self.update_signal.emit("Attempting to connect...")
            sock = None

            try:
                # 블루투스 소켓 생성 및 연결
                sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                sock.connect((mac, port))
                self.update_signal.emit("Connected!")

                # 연결 시 'connected.mp3' 재생
                self.play_mp3("connected.mp3")

                while True:
                    try:
                        # 블루투스 데이터 수신
                        data = sock.recv(1024)
                        if data:
                            received_data = data.decode('utf-8').strip()
                            self.update_signal.emit(f"Received: {received_data}")

                            # 현재 실행 중인 MP3 종료
                            self.stop_current_mp3()

                            # **VLC가 완전히 종료되도록 대기 (해결책 추가)**
                            time.sleep(0.5)

                            # 새로운 MP3 재생
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
                    except bluetooth.BluetoothError as e:
                        self.update_signal.emit(f"Connection lost: {e}")
                        break  # 연결이 끊어지면 다시 시도

            except bluetooth.BluetoothError as e:
                self.update_signal.emit(f"Connection failed: {e}\nRetrying in 5 seconds...")
                time.sleep(5)

            finally:
                # 연결이 끊어지면 'disconnected.mp3' 실행
                self.stop_current_mp3()
                self.play_mp3("disconnected.mp3")

                # 소켓 종료
                if sock:
                    sock.close()

    def find_usb_with_final(self):
        """ 연결된 USB에서 'final/' 폴더가 있는 경로 찾기 """
        base_path = "/media/pi/"
        
        # 현재 마운트된 USB 목록 가져오기
        usb_list = os.listdir(base_path)

        for usb in usb_list:
            usb_path = os.path.join(base_path, usb, "final")
            if os.path.exists(usb_path):  # 'final/' 폴더가 있는 USB 찾기
                return usb_path

        return None  # 'final/' 폴더가 있는 USB를 찾지 못한 경우

    def play_mp3(self, filename):
        """ USB에서 'final/' 폴더를 찾고, MP3 파일을 실행 """

        usb_path = self.find_usb_with_final()

        if usb_path:
            file_path = os.path.join(usb_path, filename)

            if os.path.exists(file_path):
                self.update_signal.emit(f"Playing {file_path}")

                # VLC를 실행하여 MP3 재생
                subprocess.run(["cvlc", "--play-and-exit", file_path])

            else:
                self.update_signal.emit(f"File not found: {file_path}")
        else:
            self.update_signal.emit("No USB with 'final/' folder found.")

    def stop_current_mp3(self):
        """ 현재 실행 중인 MP3 종료 """
        if self.current_process:
            self.update_signal.emit("Stopping current MP3 playback")
            self.current_process.terminate()  # VLC 종료
            self.current_process.wait()  # 종료될 때까지 대기
            self.current_process = None  # 실행 중인 프로세스 초기화

            # **VLC가 완전히 종료되도록 추가 대기**
            time.sleep(0.5)

class BluetoothApp(QWidget):
    def __init__(self):
        super().__init__()

        # PyQt5 GUI 설정
        self.setWindowTitle("Bluetooth MP3 Player")
        self.setGeometry(100, 100, 400, 200)

        # QLabel로 상태 표시
        self.label = QLabel("Waiting for Bluetooth connection...", self)
        self.label.setStyleSheet("font-size: 16px; color: blue;")

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # 블루투스 스레드 실행
        self.worker = BluetoothWorker()
        self.worker.update_signal.connect(self.update_label)
        self.worker.start()

    def update_label(self, message):
        """ QLabel을 통해 상태 메시지 업데이트 """
        self.label.setText(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 앱 실행
    window = BluetoothApp()
    window.show()

    sys.exit(app.exec_())
