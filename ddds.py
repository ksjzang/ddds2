import os
import subprocess
import time

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
