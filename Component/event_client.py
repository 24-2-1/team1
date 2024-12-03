import socket

class EventClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.login_user = None
        

    def connect(self):
        """서버에 연결"""
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Error connecting to server: {e}")

    def send_request(self, request):
        """서버로 요청 전송"""
        try:
            # request가 리스트인 경우, 이를 문자열로 변환
            if isinstance(request, list):
                request = "\n".join(str(item) for item in request)  # 리스트를 문자열로 변환

            # 이제 request는 문자열이므로, encode()를 안전하게 사용할 수 있음
            self.client_socket.sendall(request.encode())  # 문자열로 변환한 후 encode
            response = self.client_socket.recv(1024).decode()  # 응답 받기
            return response
        except Exception as e:
            print(f"Error during communication with server: {e}")
            return None
        
    def close(self):
        """서버 연결 종료"""
        self.client_socket.close()
        print("Connection closed")

    def register(self):
        """회원가입 요청 처리"""
        while True:
            print("메뉴창으로 돌아가려면 0번 입력")
            name = input("Enter userid: ")
            if name == "0":
                self.run_menu()
            print("id를 다시 입력하려면 0번 입력")
            password = input("Enter password: ")
            if password == "0":
                self.register()
            command = f"register {name} {password}"
            response = self.send_request(command)
            print(f"Server response: {response}")

            if "already exists" in response:
                print("이미 회원가입하셨습니다.")
            else:
                break

    def login(self):
        """로그인 요청 처리"""
        print("이전 화면으로 가시려면 0번 입력")
        while True:
            name = input("Enter userid: ")
            if name == "0":
                self.run_menu()
            password = input("Enter password: ")
            command = f"login {name} {password}"
            response = self.send_request(command)
            if response == "로그인 실패":
                print(response)
            else:
                self.login_user = response
                print("로그인 성공")
                break  # while 문을 종료

    def view_events(self):
        """이벤트 목록 조회"""
        command = "view_events"
        response = self.send_request(command)

        print(f"Available events:\n{response}")  # 서버에서 받은 응답 출력
        input("메뉴를 보시겠습니까")
        self.run_menu()



    def check_notifications(self):
        """알림 확인"""
        command = "check_notifications"
        response = self.send_request(command)
        print(f"Notifications:\n{response}")

    def book_event(self):
        """이벤트 예약"""
        event_id = input("Enter event ID to book: ")
        command = f"book_event {event_id}"
        response = self.send_request(command)
        print(f"Server response: {response}")
        
"""테스트"""
if __name__ == "__main__":
    client = EventClient()
    client.connect()

    while True:
        print("\nAvailable options:")
        print("1. 회원가입")
        print("2. 로그인")
        print("3. 종료하기")
        print("4. 이벤트 목록")
        print("5. 알림확인")
        print("6. 예약하기")
        
        choice = input("Enter your choice: ")

        if choice == "1":
            client.register()
        elif choice == "2":
            client.login()
        elif choice == "3":
            break
        elif choice == "4":
            client.view_events()
        elif choice == "5":
            client.check_notifications()
        elif choice == "6":
            client.book_event()
        else:
            print("Invalid choice. Please try again.")
    client.close()