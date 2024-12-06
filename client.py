import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

class EventClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.login_user = None
        self.session = PromptSession()
        self.running = True  # 클라이언트 실행 상태
        

    def connect(self):
        """서버에 연결"""
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Error connecting to server: {e}")

    def send(self, data):
        """서버로 요청 전송"""
        try:
            self.client_socket.sendall(data.encode('utf-8')) 
        except Exception as e:
            print(f"메시지 전송 중 오류 발생: {e}")
    
    def receive(self):
        """서버로부터 메시지 수신"""
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
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
        self.client_socket.close()
        print("서버 연결 종료.")
  
class ViewClient(EventClient):
    def __init__(self):
        super().__init__()
    
    def register(self):
        """회원가입 요청 처리"""
        while True:
            print("메뉴창으로 돌아가려면 0번 입력")
            name = self.session.prompt("아이디 입력: ").strip()
            if name == "0":
                self.run_menu()
            print("id를 다시 입력하려면 0번 입력")
            password = self.session.prompt("비밀번호 입력: ").strip()
            if password == "0":
                self.register()
            else:
                command = f"register {name} {password}"
                self.send(command)
                response = self.client_socket.recv(1024).decode('utf-8')
                print(f"{response} 회원가입 성공")

            if "already exists" in response:
                print("이미 회원가입하셨습니다.")
            else:
                break

    def login(self):
        """로그인 요청 처리"""
        print("이전 화면으로 가시려면 0번 입력")
        while True:
            userid = self.session.prompt("아이디 입력: ").strip()
            if userid == "0":
                self.run_menu()
            password = self.session.prompt("비밀번호 입력: ").strip()
            command = f"login {userid} {password}"
            self.send(command)
            response = self.client_socket.recv(1024).decode('utf-8')
            if response == "로그인 실패":
                print(response)
            else:
                self.login_user = response
                self.start_receive_thread()  # 로그인 후 메시지 수신 쓰레드 시작
                print("로그인 성공")
                break  # while 문을 종료

    def view_events(self):
        """이벤트 목록 조회"""
        command = "view_events"
        response = self.send(command)

        print(f"Available events:\n{response}")  # 서버에서 받은 응답 출력
        self.session.prompt("메뉴를 보시겠습니까")
        self.run_menu()

    def check_notifications(self):
        """알림 확인"""
        command = "check_notifications"
        response = self.send(command)
        print(f"Notifications:\n{response}")

    def reserve_ticket(self):
        """이벤트 예약"""
        event_id = self.session.prompt("Enter event ID to reserve: ")
        command = f"reserve_ticket {self.login_user} {event_id}"
        self.send(command)
        response = self.client_socket.recv(1024).decode('utf-8')
        if not response:
            print("Error: No response from server.")
        else:
            print(f"Server response: {response}")
        
    def cancel_reserve(self):
        """이벤트 취소"""
        event_id = self.session.prompt("Enter event ID to cancel_event: ")
        command = f"cancel {self.login_user} {event_id}"
        self.send(command)
        response = self.client_socket.recv(1024).decode('utf-8')
        print(f"Server response: {response}")
    
    def show_initial_menu(self):
        """초기 메뉴를 화면에 출력하는 함수"""
        print("\n===== 초기 메뉴 =====")
        print("1. 회원가입")  # 회원가입 선택지
        print("2. 로그인")  # 로그인 선택지
        print("3. 뮤지컬 목록 보기") 
        print("0. 종료")  # 프로그램 종료 선택지

    def show_logged_in_menu(self):
        """로그인 후 사용자 메뉴를 화면에 출력하는 함수"""
        print("\n===== 로그인 후 메뉴 =====")
        print("1. 뮤지컬 목록 보기")  # 대기자 등록 선택지
        print("2. 티켓 예약")  # 티켓 예약 선택지
        print("3. 예약 취소")  # 예약 취소 선택지
        print("4. 알림 확인")  # 알림 확인 선택지
        print("9. 로그아웃")  # 로그아웃 선택지
        print("0. 종료")  

    def handle_guest_action(self, choice):
        """로그인하지 않은 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.register,  # 회원가입 처리
            "2": self.login,  # 로그인 처리
            "3": self.view_events, #뮤지컬 목록
        }
        return self._handle_action(actions, choice)  # 선택한 액션 처리
    
    def handle_user_action(self, choice):
        """로그인한 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.view_events,  # 이벤트 목록
            "2": self.reserve_ticket,  # 티켓 예약 처리
            "3": self.cancel_reserve,  # 티켓 취소 처리
            "4": self.check_notifications,  # 알림 확인 처리
            "9": self.logout,  # 로그아웃 처리
        }
        return self._handle_action(actions, choice)  # 선택한 액션 처리


    def _handle_action(self, actions, choice):
        """공통된 행동 처리 로직: 유효한 선택인지 확인 후 해당 처리 함수 호출"""
        action = actions.get(choice)  # 사용자가 선택한 옵션에 맞는 액션을 찾음
        if action:
            action()  # 선택한 액션을 실행
            return True
        else:
            print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리
            return False
    
    def logout(self):
        self.login_user = None
    
    def run_menu(self):
        """프로그램 실행 함수: 사용자 선택에 따라 메뉴를 반복 출력하며 처리"""
        while True:
            if self.login_user:
                # 로그인된 상태에서 메뉴 출력
                self.show_logged_in_menu()
                choice = self.session.prompt("메뉴를 선택하세요: ").strip()
                if choice == "0":
                    print("프로그램을 종료합니다.")
                    self.close()  # 연결 종료
                    exit()  # 프로그램 완전히 종료
                if not self.handle_user_action(choice):  # 잘못된 선택 시 다시 시도
                    continue
            else:
                # 로그인되지 않은 상태에서 메뉴 출력
                self.show_initial_menu()
                choice = self.session.prompt("메뉴를 선택하세요: ").strip()
                if choice == "0":
                    print("프로그램을 종료합니다.")
                    self.close()  # 연결 종료
                    exit()  # 프로그램 완전히 종료
                if not self.handle_guest_action(choice):  # 잘못된 선택 시 프로그램 종료
                    continue


if __name__ == "__main__":
    client = ViewClient()
    client.connect()
    client.run_menu()
