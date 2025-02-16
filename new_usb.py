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

    def __init__(self):
        super().__init__()
        self.vlc_process = None  # VLC 프로세스 핸들
        self.running = True  # 스레드 실행 상태

    def stop_current_mp3(self):
        """ 현재 실행 중인 MP3를 강제로 중지 """
        if self.vlc_process:
            self.vlc_process.terminate()  # VLC 프로세스 종료
            self.vlc_process.wait()  # 종료 완료 대기
            self.vlc_process = None

    def find_final_folder(self):
        """ USB 장치에서 'final' 폴더의 경로를 찾음 """
        base_path = "/media/pi/"
        if not os.path.exists(base_path):
            return None  # USB 경로 없음

        for usb_name in os.listdir(base_path):
            usb_path = os.path.join(base_path, usb_name)
            final_path = os.path.join(usb_path, "final")

            if os.path.isdir(final_path):  # 'final' 폴더가 존재하면 반환
                return final_path

        return None  # 'final' 폴더를 찾지 못함

    def connect_bluetooth(self):
        """ 블루투스 연결을 시도하고 성공할 때까지 반복 """
        mac = '08:D1:F9:26:65:D2'
        port = 1

        while self.running:
            try:
                self.update_signal.emit("Attempting to connect...")
                sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                sock.connect((mac, port))
                self.update_signal.emit("Connected")
                return sock  # 연결된 소켓 반환
            except bluetooth.BluetoothError as e:
                self.update_signal.emit(f"Connection failed: {e}\nRetrying in 5 seconds...")
                time.sleep(5)

    def run(self):
        """ 블루투스 메시지를 수신하고 MP3를 재생 """
        while self.running:
            sock = self.connect_bluetooth()  # 블루투스 연결 시도

            try:
                while self.running:
                    data = sock.recv(1024).decode('utf-8').strip()

                    # 빈 데이터 또는 공백만 있는 데이터가 들어오면 무시
                    if not data:
                        self.update_signal.emit("Warning: Received empty data. Ignoring...")
                        continue

                    # 블루투스에서 받은 데이터 로그 출력
                    self.update_signal.emit(f"Received: {data}")

                    # 'final' 폴더의 경로 찾기
                    final_folder = self.find_final_folder()
                    if not final_folder:
                        self.update_signal.emit("USB with 'final' folder not found.")
                        continue

                    # MP3 파일 경로 설정
                    mp3_files = {
                        '1': os.path.join(final_folder, "stemon1.mp3"),
                        '2': os.path.join(final_folder, "stemon2.mp3"),
                        '3': os.path.join(final_folder, "stemon3.mp3"),
                        '4': os.path.join(final_folder, "stemon4.mp3"),
                    }
                    try:
                        # 받은 데이터가 '1'~'4'인지 확인 후 실행
                        if data in mp3_files:
                                mp3_path = mp3_files[data]

                                # 파일이 존재하는지 확인 후 실행
                                if os.path.exists(mp3_path):
                                    self.stop_current_mp3()  # 기존 MP3 강제 종료
                                    self.update_signal.emit(f"Playing {data}.mp3")
                                    self.vlc_process = subprocess.Popen(
                                        ["cvlc", "--play-and-exit", mp3_path],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                                    )
                                else:
                                    self.update_signal.emit(f"Error: File not found - {mp3_path}")
                    except:
                        self.update_signal.emit(f"Warning: Invalid data received - '{data}'. Ignoring...")

            except bluetooth.BluetoothError:
                self.update_signal.emit("Connection lost. Reconnecting...")
            finally:
                sock.close()  # 연결 종료 후 다시 연결 시도

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
