import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

HOST = '127.0.0.1'
PORT = 65433

class Client:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logged_in = False
        self.userid = None
        self.session = PromptSession()
        self.running = True  # 클라이언트 실행 상태

    def connect(self):
        self.socket.connect((HOST, PORT))
        print("서버에 연결되었습니다.")

    def send(self, data):
        """서버로 메시지 전송"""
        self.socket.sendall(data.encode('utf-8'))

    def receive(self):
        """서버로부터 메시지 수신"""
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    print("\n서버 연결이 끊어졌습니다.")
                    break
                print(f"\n[서버 메시지]: {data}")
            except Exception as e:
                print(f"메시지 수신 중 오류 발생: {e}")
                break

    def start_receive_thread(self):
        """메시지 수신용 쓰레드 시작"""
        recv_thread = threading.Thread(target=self.receive, daemon=True)
        recv_thread.start()

    def close(self):
        """서버 연결 종료"""
        self.running = False
        self.socket.close()
        print("서버 연결 종료.")

    def menu(self):
        """메뉴 출력 및 선택"""
        while True:
            print("\n1. 회원가입")
            print("2. 로그인")
            print("3. 종료")
            choice = self.session.prompt("선택: ").strip()

            if choice == '1':
                self.register()
            elif choice == '2':
                self.login()
            elif choice == '3':
                self.close()
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")

    def register(self):
        """회원가입"""
        userid = self.session.prompt("아이디 입력: ").strip()
        password = self.session.prompt("비밀번호 입력: ").strip()
        self.send(f"REGISTER:{userid}:{password}")
        response = self.socket.recv(1024).decode('utf-8')
        print(response)

    def login(self):
        """로그인"""
        userid = self.session.prompt("아이디 입력: ").strip()
        password = self.session.prompt("비밀번호 입력: ").strip()
        self.send(f"LOGIN:{userid}:{password}")
        response = self.socket.recv(1024).decode('utf-8')
        print(response)
        if response == "로그인 성공":
            self.logged_in = True
            self.userid = userid
            self.start_receive_thread()  # 로그인 후 메시지 수신 쓰레드 시작
            self.messaging_menu()

    def messaging_menu(self):
        """메시지 전송 메뉴"""
        print("메시지를 보내려면 '대상이름:메시지' 형식으로 입력하세요.")
        print("프로그램을 종료하려면 'exit'을 입력하세요.")
        with patch_stdout():
            while self.logged_in:
                try:
                    message = self.session.prompt("> ").strip()
                    if message.lower() == 'exit':
                        print("메시징 메뉴를 종료합니다.")
                        break
                    if ':' in message:
                        self.send(f"MESSAGE:{message}")
                    else:
                        print("잘못된 형식입니다. '대상이름:메시지' 형식으로 입력하세요.")
                except (EOFError, KeyboardInterrupt):
                    print("\n메시징 메뉴를 종료합니다.")
                    break


def main():
    client = Client()
    client.connect()
    client.menu()


if __name__ == "__main__":
    main()