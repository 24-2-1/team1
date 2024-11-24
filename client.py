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


if __name__ == "__main__":
    client = EventClient()
    client.connect()

    while True:
        print("\nAvailable options:")
        print("1. Register")
        print("2. Login (Not implemented)")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            client.register()
        elif choice == "2":
            print("Login functionality is not implemented yet.")
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")

    client.close()
