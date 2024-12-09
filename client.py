import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import subprocess 

class EventClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.login_user = None
        self.session = PromptSession()
        self.queue = asyncio.Queue()  # 수신 데이터를 관리할 큐

    async def connect(self):
        if self.writer is not None:
            print("이미 서버에 연결되어 있습니다.")
            return
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
        """서버로부터 메시지 수신 (중앙 루프)"""
        try:
            while True:
                data = await self.reader.read(1024)
                if not data:
                    print("\n서버 연결이 끊어졌습니다.")
                    break
                msg = data.decode('utf-8')
                # 명령 응답(response:)과 알림(notify:) 구분
                if msg.startswith("response:"):
                    # response: 이후 내용만 queue에 넣음
                    await self.queue.put(msg[len("response:"):].strip())
                elif msg.startswith("notify:"):
                    # notify: 이후 내용은 별도 처리(알림 출력용)
                    # 알림 출력용 큐나 별도 처리를 위한 구조 필요
                    # 여기서는 간단히 알림을 바로 출력 (prompt_toolkit 상태에서는 print 사용 주의)
                    print(f"[서버 알림]: {msg[len('notify:'):].strip()}")
                else:
                    # 구분자가 없으면 일단 응답으로 처리
                    await self.queue.put(msg.strip())
        except Exception as e:
            print(f"메시지 수신 중 오류 발생: {e}")

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
        check_register=None
        while True:
            print("메뉴창으로 돌아가려면 0번 입력")
            name = await self.session.prompt_async("아이디 입력: ")
            name = name.strip()
            if name == "0":
                break # 메뉴로 돌아감
            
            if not name:
                print("아이디를 입력해야 합니다. 다시 시도해주세요.")
                continue  # 아이디 입력이 없으면 다시 입력 받음

            while True:
                password = await self.session.prompt_async("비밀번호 입력: ")
                password = password.strip()
                if password == "0":
                    break

                if not password:
                    print("비밀번호는 비워둘 수 없습니다. 다시 입력하세요.")
                    continue  # 비밀번호 입력이 없으면 다시 입력 받음

                # 비밀번호가 정상적으로 입력되었을 때만 서버로 요청
                command = f"register {name} {password}"
                await self.send(command)
                response = await self.get_response()  # 큐에서 응답 가져오기

                if "already exists" in response:
                    print("이미 회원가입하셨습니다.")  # 이미 회원가입된 경우 처리
                    break  # 회원가입 절차 종료
                else:
                    print(f"{response} 회원가입 성공")  # 성공 메시지 출력
                    check_register = True
                    break  # 회원가입이 성공하면 종료
            if check_register:
                break  # 성공적으로 회원가입되었으면 종료

    async def login(self):
        """로그인 요청 처리"""
        print("이전 화면으로 가시려면 0번 입력")
        while True:
            userid = await self.session.prompt_async("아이디 입력: ")
            userid = userid.strip()
            if userid == "0":
                return

            if not userid:
                print("아이디를 입력해야 합니다. 다시 시도해주세요.")
                continue  # 아이디 입력이 없으면 다시 입력 받음

            while True:
                password = await self.session.prompt_async("비밀번호 입력: ")
                password = password.strip()
                if not password:
                    print("비밀번호는 비워둘 수 없습니다. 다시 입력하세요.")
                    continue  # 비밀번호 입력이 없으면 다시 입력 받음
                elif password == "0":
                    break  # 비밀번호 입력 창에서 '0'을 누르면 아이디 입력 창으로 돌아감
                
                command = f"login {userid} {password}"
                await self.send(command)
                response = await self.get_response()  # 큐에서 응답 가져오기
                
                if response == "로그인 실패":
                    print(response)
                else:
                    self.login_user = response
                    print("로그인 성공")
                    break
            if self.login_user:  # 로그인 성공 시 빠져나옴
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
        event_id = await self.session.prompt_async("event_id 입력: ")
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
        await self.session.prompt_async("메뉴로 돌아가려면 [Enter]")
             
    async def reserve_ticket(self):
        """티켓 예약"""
        check_reserve = None
        while True:
            event_id = await self.session.prompt_async("Enter event ID to reserve: ")
            if not event_id:
                print("이벤트 ID는 비워둘 수 없습니다. 다시 입력하세요.")  # 수정됨
                continue    
            command = f"view_seat {event_id}"
            await self.send(command)
            response = await self.get_response()  # 큐에서 응답 가져오기
            if response == "이벤트를 잘못 선택하셨습니다.":
                print(response)
                continue
            print(response)
            # 예약할 좌석을 입력받음
            while True:
                seat_number = await self.session.prompt_async("좌석번호 입력: ex) A1, B1, C3): ")  # 좌석 번호 입력 받기
                if not seat_number:
                    print("좌석 번호는 비워둘 수 없습니다. 다시 입력하세요.")  # 수정됨
                    continue
                command = f"reserve_ticket {self.login_user} {event_id} {seat_number}"  # 좌석 번호를 포함한 명령어 전송
                await self.send(command)
                response = await self.get_response()  # 큐에서 응답 가져오기
                if response == "티켓 예약 성공" or response == "대기자로 갔어":
                    check_reserve = True
                    print(response)
                    break
                else:
                    print(response)     
            if check_reserve == True:
                break
                 
        
    async def cancel_reserve(self):
        """이벤트 취소"""
        while True:
            event_id = await self.session.prompt_async("Enter event ID to cancel_event: ")
            if not event_id:
                print("이벤트 ID는 비워둘 수 없습니다. 다시 입력하세요.")  # 수정됨
                continue
            command = f"cancel {self.login_user} {event_id}"
            await self.send(command)
            response = await self.get_response()  # 큐에서 응답 가져오기
            print(response)
            break
            
    async def run_manage_function(self):
        """관리장 실행"""
        try:
            print("관리장을 실행합니다...")
            subprocess.run(["python", "DB/manage.py"], check=True)  # manage.py 실행
        except subprocess.CalledProcessError as e:
            print(f"관리장 실행 중 오류 발생: {e}")
            
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
            "/": self.run_manage_function,  # 관리장 실행 추가
        }
        return await self._handle_action(actions, choice)  # 선택한 액션 처리

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
            await action()
            return True
        else:
            print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리
            return False        
        
    async def run_menu(self):
        """메뉴 실행"""
        asyncio.create_task(self.receive())  # 수신 루프를 백그라운드에서 실행
        # asyncio.create_task(self.print_incoming_messages())
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
                    print("/. 관리장 실행")  # 관리장 메뉴 추가
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
        if not self.writer:
            await self.connect()
        await self.run_menu()

if __name__ == "__main__":
    client = ViewClient()
    try:
        # 실행 중인 이벤트 루프를 가져옵니다.
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행 중인 루프에서는 create_task로 비동기 작업을 추가합니다.
            loop.create_task(client.main())
        else:
            # 새로운 이벤트 루프를 실행합니다.
            loop.run_until_complete(client.main())
    except RuntimeError as e:
        print(f"RuntimeError 발생: {e}")


