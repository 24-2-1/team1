import asyncio
import json
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

class EventClient:
    """서버와의 통신을 담당하는 클래스."""
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.login_user = None
        self.message_callback = None
        self.lock = asyncio.Lock()

    async def connect(self):
        """서버 연결"""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            print(f"Connected to server at {self.host}:{self.port}")
            asyncio.create_task(self.receive_messages())
        except Exception as e:
            print(f"Error connecting to server: {e}")

    async def receive_messages(self):
        """서버 메시지 수신"""
        try:
            while True:
                data = await self.reader.read(1024)
                if not data:
                    print("Connection closed by server.")
                    break
                message = json.loads(data.decode().strip())
                if "type" in message and "data" in message:
                    # 메시지 처리 (예: 알림과 응답 분리)
                    if message["type"] == "notification":
                        print(f"\n[알림] {message['data']}\n> ", end='', flush=True)
                    else:
                        # 요청에 대한 응답 처리
                        if self.message_callback:
                            await self.message_callback(message["data"])
                else:
                    print(f"Invalid message from server: {message}")
        except Exception as e:
            print(f"Error receiving message from server: {e}")

    async def send_request(self, command_type, data):
        """서버에 JSON 요청 전송"""
        async with self.lock:
            try:
                request_data = json.dumps({"type": command_type, "data": data})
                self.writer.write(request_data.encode())
                await self.writer.drain()
            except Exception as e:
                print(f"Error during communication with server: {e}")
                return {"status": "error", "message": str(e)}


    async def close(self):
        """서버 연결 종료"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            print("Connection closed")

    def set_message_callback(self, callback):
        self.message_callback = callback


class ViewClient:
    """사용자 인터페이스"""
    def __init__(self):
        self.client = EventClient()
        self.client.set_message_callback(self.handle_server_message)
        self.session = PromptSession()

    async def handle_server_message(self, message):
        """서버 메시지 처리"""
        print(f"\n[알림] {message}\n> ", end='', flush=True)

    async def run_menu(self):
        """메인 메뉴"""
        await self.client.connect()
        with patch_stdout():
            while True:
                if self.client.login_user:
                    self.show_logged_in_menu()
                    choice = (await self.session.prompt_async("> ")).strip()
                    if choice == "0":
                        await self.client.close()
                        break
                    await self.handle_user_action(choice)
                else:
                    self.show_initial_menu()
                    choice = (await self.session.prompt_async("> ")).strip()
                    if choice == "0":
                        await self.client.close()
                        break
                    await self.handle_guest_action(choice)

    def show_initial_menu(self):
        """초기 메뉴 표시"""
        print("\n===== 초기 메뉴 =====")
        print("1. 회원가입")
        print("2. 로그인")
        print("3. 이벤트 목록 보기")
        print("0. 종료")

    def show_logged_in_menu(self):
        """로그인 후 메뉴 표시"""
        print("\n===== 로그인 후 메뉴 =====")
        print("1. 이벤트 목록 보기")
        print("2. 티켓 예약")
        print("3. 알림 확인")
        print("4. 예약 취소")
        print("9. 로그아웃")
        print("0. 종료")

    async def handle_guest_action(self, choice):
        """비로그인 사용자 액션"""
        if choice == "1":
            await self.handle_authentication("register")
        elif choice == "2":
            await self.handle_authentication("login")
        elif choice == "3":
            await self.view_events()
        else:
            print("잘못된 입력입니다. 다시 시도하세요.")

    async def handle_user_action(self, choice):
        """로그인 사용자 액션"""
        if choice == "1":
            await self.view_events()
        elif choice == "2":
            await self.reserve_ticket()
        elif choice == "3":
            print("실시간 알림은 자동으로 표시됩니다.")
        elif choice == "4":
            await self.cancel_reservation()
        elif choice == "9":
            self.logout()
        else:
            print("잘못된 입력입니다. 다시 시도하세요.")

    async def handle_authentication(self, mode):
        """회원가입 및 로그인"""
        while True:
            name = (await self.session.prompt_async("Enter userid: ")).strip()
            if name == "0":
                return
            password = (await self.session.prompt_async("Enter password: ")).strip()
            response = await self.client.send_request(mode, {"userid": name, "password": password})
            print(response.get("message", "응답 오류"))
            if response.get("status") == "success":
                if mode == "login":
                    self.client.login_user = name
                break

    async def view_events(self):
        """이벤트 목록 보기"""
        response = await self.client.send_request("view_events", {})
        print(response.get("message", "응답 오류"))

    async def reserve_ticket(self):
        """티켓 예약"""
        event_id = await self.session.prompt_async("Enter event ID: ")
        response = await self.client.send_request("reserve_ticket", {"userid": self.client.login_user, "event_id": event_id})
        print(response.get("message", "응답 오류"))

    async def cancel_reservation(self):
        """예약 취소"""
        event_id = await self.session.prompt_async("Enter event ID to cancel: ")
        response = await self.client.send_request("cancel", {"userid": self.client.login_user, "event_id": event_id})
        print(response.get("message", "응답 오류"))

    def logout(self):
        """로그아웃"""
        self.client.login_user = None
        print("로그아웃 되었습니다.")


if __name__ == "__main__":
    client = ViewClient()
    asyncio.run(client.run_menu())
