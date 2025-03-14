#!/usr/bin/env python3
import bluetooth
import time
import subprocess
import sys
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
                    data = sock.recv(1024)
                    if data:
                        received_data = data.decode('utf-8').strip()
                        self.update_signal.emit(f"Received: {received_data}")

                        # 수신된 번호에 해당하는 MP3 파일 매핑
                        mp3_files = {
                            '1': "/media/pi/3460-A639/final/stemon1.mp3",
                            '2': "/media/pi/3460-A639/final/stemon2.mp3",
                            '3': "/media/pi/3460-A639/final/stemon3.mp3",
                            '4': "/media/pi/3460-A639/final/stemon4.mp3",
                        }

                        if received_data in mp3_files:
                            self.stop_current_mp3()  # 기존 MP3 강제 종료
                            self.update_signal.emit(f"Playing {received_data}.mp3")
                            self.vlc_process = subprocess.Popen(
                                ["cvlc", "--play-and-exit", mp3_files[received_data]],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )

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
