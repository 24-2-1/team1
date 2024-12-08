import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

class EventClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reader = None
        self.writer = None
        self.login_user = None
        self.session = PromptSession()
        self.running = True  # 클라이언트 실행 상태
        self.queue = asyncio.Queue()  # 수신 데이터를 관리할 큐

    async def connect(self):
        """서버에 연결"""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            print(f"서버에 연결되었습니다: {self.host}:{self.port}")
        except Exception as e:
            print(f"서버 연결 중 오류 발생: {e}")

    async def send(self, data):
        """서버로 요청 전송"""
        try:
            self.writer.write(data.encode('utf-8'))
            await self.writer.drain()
        except Exception as e:
            print(f"메시지 전송 중 오류 발생: {e}")

    async def receive(self):
        """서버로부터 메시지 수신"""
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    print("\n서버 연결이 끊어졌습니다.")
                    self.running = False
                    break
                with patch_stdout():
                    print(f"\n[서버 메시지]: {data}")
            except Exception as e:
                print(f"메시지 수신 중 오류 발생: {e}")
                self.running = False
                break

    def start_receive_thread(self):
        """메시지 수신용 쓰레드 시작"""
        recv_thread = threading.Thread(target=self.receive, daemon=True)

    async def get_response(self):
        """큐에서 서버 응답 가져오기"""
        try:
            response = await self.queue.get()  # 큐에서 데이터 가져오기
            return response
        except Exception as e:
            print(f"응답 처리 중 오류 발생: {e}")
            
    async def close(self):
        """연결 종료"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        print("서버 연결 종료.")
        
class ViewClient(EventClient):      
    def __init__(self):
        super().__init__()
         
    async def register(self):
        """회원가입 요청 처리"""
        while True:
            print("메뉴창으로 돌아가려면 0번 입력")
            name = await self.session.prompt_async("아이디 입력: ").strip()
            name = name.strip()
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

    async def login(self):
        """로그인 요청 처리"""
        print("이전 화면으로 가시려면 0번 입력")
        while True:
            userid = await self.session.prompt_async("아이디 입력: ")
            userid = userid.strip()
            if userid == "0":
                return
            password = await self.session.prompt_async("비밀번호 입력: ")
            password = password.strip()
            command = f"login {userid} {password}"
            await self.send(command)
            response = await self.get_response()  # 큐에서 응답 가져오기
            if response == "로그인 실패":
                print(response)
            else:
                self.login_user = response
                print("로그인 성공")
                print(response)
                break
            
    async def logout(self):
        """로그아웃 요청 처리"""
        if not self.login_user:
            print("로그인 중이 아닌데")
            return
        command = f"logout {self.login_user}"
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        if response:
            print(response)
            self.login_user = None  # 클라이언트 상태 업데이트
            
    async def view_events(self):
        """이벤트 목록 조회"""
        command = "view_events"
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(response)
        await self.session.prompt_async("메뉴로 돌아가려면 [Enter]")
        
    async def view_seat_availability(self):
        """이벤트 좌석 현황 조회"""
        event_id = self.session.prompt("event_id 입력: ")
        event_id = event_id.strip()
        command = f"view_seat {event_id}"
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(response)
        
    async def check_reservation_status(self):
        """예약 현황 조회"""
        command = f"check_reservation_status {self.login_user}"
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(response)      
          
    async def view_events(self):
        """이벤트 목록 조회"""
        command = "view_events"
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(response)  # 서버에서 받은 응답 출력

    async def check_log(self):
        """알림 확인"""
        # 로그인한 사용자의 ID를 기반으로 알림 요청
        command = f"check_log {self.login_user}"
        await self.send(command)
        
        # 서버에서 받은 응답 처리
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(f"사용자 기록:\n{response}")
        print(response)  # 서버에서 받은 응답 출력
        await self.session.prompt("메뉴로 돌아가려면 [Enter]")
             
    async def reserve_ticket(self):
        """티켓 예약"""
        event_id = await self.session.prompt("Enter event ID to reserve: ")
        command = f"view_seat {event_id}"
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(response)
        # 예약할 좌석을 입력받음
        seat_number = await self.session.prompt("좌석번호 입력: ex) A1, B1, C3): ")  # 좌석 번호 입력 받기
        command = f"reserve_ticket {self.login_user} {event_id} {seat_number}"  # 좌석 번호를 포함한 명령어 전송
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(response)          
        
    async def cancel_reserve(self):
        """이벤트 취소"""
        event_id = await self.session.prompt("Enter event ID to cancel_event: ")
        command = f"cancel {self.login_user} {event_id}"
        await self.send(command)
        response = await self.get_response()  # 큐에서 응답 가져오기
        print(response)  
               
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
        print("2. 좌석 현황 조회")  # 좌석현황조회 선택지
        print("3. 티켓 예약")  # 티켓 예약 선택지
        print("4. 예약 취소")  # 예약 취소 선택지
        print("5. 기록 확인")  # 알림 확인 선택지
        print("6. 예약 현황 조회")
        print("9. 로그아웃")  # 로그아웃 선택지
        print("0. 종료")  

    async def handle_guest_action(self, choice):
        actions = {
            "1": self.register,  # 회원가입 처리
            "2": self.login,  # 로그인 처리
            "3": self.view_events, #뮤지컬 목록
        }
        return self._handle_action(actions, choice)  # 선택한 액션 처리

    async def handle_user_action(self, choice):
        """로그인한 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.view_events,  # 이벤트 목록
            "2": self.view_seat_availability,  # 좌석 현황 조회 처리
            "3": self.reserve_ticket,  # 티켓 예약 처리
            "4": self.cancel_reserve,  # 티켓 취소 처리
            "5": self.check_log,  # 알림 확인 처리
            "6": self.check_reservation_status,  # 예약 현황 조회 추가
            "9": self.logout,  # 로그아웃 처리
        }
        return await self._handle_action(actions, choice)  # 선택한 액션 처리
    
    async def _handle_action(self, actions, choice):
        """공통된 행동 처리 로직: 유효한 선택인지 확인 후 해당 처리 함수 호출"""
        action = actions.get(choice)  # 사용자가 선택한 옵션에 맞는 액션을 찾음
        if action:
            action()  # 선택한 액션을 실행
            return True
        else:
            print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리
            return False        
        
    async def run_menu(self):
        """메뉴 실행"""
        asyncio.create_task(self.receive())  # 수신 루프를 백그라운드에서 실행
        while True:
            try:
                if self.login_user:
                    self.show_logged_in_menu()
                    with patch_stdout():
                        choice = await self.session.prompt_async("메뉴를 선택하세요: ")
                        choice = choice.strip()
                    if choice == "0":
                        print("프로그램을 종료합니다.")
                        await self.close()
                        break
                    await self.handle_user_action(choice)
                else:
                    self.show_initial_menu()
                    with patch_stdout():
                        choice = await self.session.prompt_async("메뉴를 선택하세요: ")
                        choice = choice.strip()
                    if choice == "0":
                        print("프로그램을 종료합니다.")
                        await self.close()
                        break
                    await self.handle_guest_action(choice)
            except Exception as e:
                print(f"메뉴 처리 중 오류 발생: {e}")
                
    async def main(self):
        """클라이언트 실행"""
        await self.connect()
        await self.run_menu()

if __name__ == "__main__":
    client = ViewClient()
    asyncio.run(client.main())
