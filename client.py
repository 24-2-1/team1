import socket


class EventClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
            self.client_socket.sendall(request.encode())
            response = self.client_socket.recv(1024).decode()
            return response
        except BrokenPipeError:
            print("Error: Connection to the server was lost.")
            return None
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
            name = input("Enter username: ")
            password = input("Enter password: ")
            command = f"register {name} {password}"
            response = self.send_request(command)
            print(f"Server response: {response}")

            if "already exists" in response:
                print("Username is already taken. Please try another one.")
            else:
                break

    def login(self):
        """로그인 요청 처리"""
        name = input("Enter username: ")
        password = input("Enter password: ")
        command = f"login {name} {password}"
        response = self.send_request(command)
        print(f"Server response: {response}")

    def view_events(self):
        """이벤트 목록 조회"""
        command = "view_events"
        response = self.send_request(command)
        print(f"Available events:\n{response}")

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


if __name__ == "__main__":
    client = EventClient()
    client.connect()

    while True:
        print("\nAvailable options:")
        print("1. 회원가입")
        print("2. 로그인")
        print("3. 종료하기")
        print("4. 이벤트 목록")
        print("5. 알림 확인")
        print("6. 예약하기")
        
        choice = input("Enter your choice: ")

        if choice == "1":
            client.register()
        elif choice == "2":
            client.login()
        elif choice == "3":
            break
        elif choice == "4":
            command = "view_events"  # command 변수 정의
            client.view_events()
            response = client.send_request(command)
            print(f"Available events:\n{response}")
        elif choice == "5":
            client.check_notifications()
        elif choice == "6":
            client.book_event()
        else:
            print("Invalid choice. Please try again.")
    client.close()
