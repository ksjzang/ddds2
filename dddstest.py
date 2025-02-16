#!/usr/bin/env python3
import bluetooth
import time
import subprocess
import sys
import os
import queue
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal

class BluetoothReceiver(QThread):
    """ 블루투스 메시지를 계속 받는 별도 스레드 """
    message_received = pyqtSignal(str)  # UI에 메시지를 전달하는 시그널

    def __init__(self, mac_address, port):
        super().__init__()
        self.mac_address = mac_address
        self.port = port
        self.sock = None
        self.running = True

    def run(self):
        """ 블루투스 연결을 유지하면서 메시지를 수신 """
        while self.running:
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

            try:
                self.sock.connect((self.mac_address, self.port))
                print("✅ 블루투스 연결됨!")

                while self.running:
                    data = self.sock.recv(1024)
                    if data:
                        received_data = data.decode('utf-8').strip()
                        print(f"🔵 수신됨: {received_data}")
                        self.message_received.emit(received_data)  # 메시지를 메인 UI로 보냄

            except bluetooth.BluetoothError as e:
                print(f"❌ 연결 실패: {e}\n5초 후 재시도...")
                time.sleep(5)

            finally:
                if self.sock:
                    self.sock.close()

    def stop(self):
        """ 블루투스 수신 스레드 중지 """
        self.running = False
        if self.sock:
            self.sock.close()

class BluetoothWorker(QThread):
    """ MP3 재생을 관리하는 스레드 """
    update_signal = pyqtSignal(str)  # UI에 메시지를 보내는 시그널
    current_process = None  # 현재 실행 중인 VLC 프로세스
    message_queue = queue.Queue()  # **블루투스 메시지를 저장하는 큐**

    def __init__(self):
        super().__init__()

    def run(self):
        """ 큐에서 메시지를 하나씩 꺼내서 MP3 재생 """
        while True:
            if not self.message_queue.empty():
                received_data = self.message_queue.get()
                print(f"🔄 처리 중: {received_data}")

                self.stop_current_mp3()  # 현재 실행 중인 MP3 즉시 중지

                # **새로운 MP3 실행**
                if received_data == '1':
                    self.update_signal.emit("🔊 Playing stemon1.mp3")
                    self.play_mp3("stemon1.mp3")
                elif received_data == '2':
                    self.update_signal.emit("🔊 Playing stemon2.mp3")
                    self.play_mp3("stemon2.mp3")
                elif received_data == '3':
                    self.update_signal.emit("🔊 Playing stemon3.mp3")
                    self.play_mp3("stemon3.mp3")
                elif received_data == '4':
                    self.update_signal.emit("🔊 Playing stemon4.mp3")
                    self.play_mp3("stemon4.mp3")

    def add_to_queue(self, received_data):
        """ 블루투스 메시지를 큐에 추가 (메시지가 씹히지 않도록 저장) """
        print(f"📝 큐에 추가: {received_data}")
        self.message_queue.put(received_data)

    def play_mp3(self, filename):
        """ MP3 파일을 USB에서 찾아 실행 """
        usb_path = self.find_usb_with_final()

        if usb_path:
            file_path = os.path.join(usb_path, filename)

            if os.path.exists(file_path):
                self.update_signal.emit(f"🎵 재생 중: {file_path}")
                print(f"🎵 MP3 실행 요청: {file_path}")

                # **기존 MP3를 완전히 종료**
                self.stop_current_mp3()

                # **디버깅 로그 추가**
                print(f"🔍 VLC 프로세스 실행 시도 (파일: {file_path})")

                # **VLC를 백그라운드가 아니라 포그라운드에서 실행 (UI에 표시됨)**
                result = subprocess.call(["cvlc", "--play-and-exit", file_path])

                # **디버깅: VLC 실행 결과 확인**
                if result == 0:
                    print(f"✅ VLC가 정상적으로 {file_path} 실행 완료!")
                else:
                    print(f"❌ VLC 실행 실패! (에러 코드: {result})")

            else:
                self.update_signal.emit(f"⚠ 파일을 찾을 수 없음: {file_path}")
                print(f"⚠ 파일 없음: {file_path}")
        else:
            self.update_signal.emit("⚠ USB에서 'final/' 폴더를 찾을 수 없음.")
            print("⚠ USB에 'final/' 폴더 없음.")

    def stop_current_mp3(self):
        """ 현재 실행 중인 MP3 즉시 종료 및 VLC 프로세스 완전 종료 확인 """
        if self.current_process:
            self.update_signal.emit("🛑 현재 MP3 재생 중지")
            print("🛑 VLC 종료 요청")

            try:
                self.current_process.kill()  # VLC 종료 시도
            except Exception as e:
                print(f"❌ VLC 종료 실패: {e}")

            self.current_process = None  # 프로세스 초기화

        # **디버깅 로그 추가**
        print("🔍 VLC 프로세스 강제 종료 시도 (pkill 실행)")
        subprocess.call(["pkill", "vlc"])  # VLC 프로세스 종료
        time.sleep(0.2)  # 종료 대기

        # **VLC 프로세스가 완전히 종료되었는지 확인**
        while subprocess.call(["pgrep", "vlc"]) == 0:  
            print("⌛ VLC 종료 대기 중...")
            time.sleep(0.1)  # 100ms 단위로 재확인

        print("✅ VLC 완전히 종료됨!")

    def find_usb_with_final(self):
        """ 'final/' 폴더가 있는 USB를 자동으로 탐색 """
        base_path = "/media/pi/"
        
        # 마운트된 USB 목록 가져오기
        usb_list = os.listdir(base_path)

        for usb in usb_list:
            usb_path = os.path.join(base_path, usb, "final")
            if os.path.exists(usb_path):  # 'final/' 폴더가 있는 USB 찾기
                return usb_path

        return None  # 'final/' 폴더가 없으면 None 반환

class BluetoothApp(QWidget):
    """ PyQt5 GUI 설정 """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bluetooth MP3 Player")
        self.setGeometry(100, 100, 400, 200)

        self.label = QLabel("블루투스 연결 대기 중...", self)
        self.label.setStyleSheet("font-size: 16px; color: blue;")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # 블루투스 및 MP3 스레드 실행
        self.worker = BluetoothWorker()
        self.receiver = BluetoothReceiver("08:D1:F9:26:65:D2", 1)

        # 블루투스 메시지를 MP3 실행 큐에 추가
        self.receiver.message_received.connect(self.worker.add_to_queue)

        # 스레드 실행
        self.worker.start()
        self.receiver.start()

        # UI 업데이트 연결
        self.worker.update_signal.connect(self.update_label)

    def update_label(self, message):
        """ UI 상태 업데이트 """
        self.label.setText(message)

    def closeEvent(self, event):
        """ 앱 종료 시 스레드 중지 """
        self.receiver.stop()
        self.worker.stop_current_mp3()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BluetoothApp()
    window.show()
    sys.exit(app.exec_())
