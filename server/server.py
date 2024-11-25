import socket
import threading
from db import initialize_database, DatabaseConnector
from user_service import UserService
from event_service import EventService

class EventServer:
    HOST = '0.0.0.0'
    PORT = 5000
    MAX_CONNECTIONS = 5

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.HOST, self.PORT))
        self.server_socket.listen(self.MAX_CONNECTIONS)
        print(f"Server started on {self.HOST}:{self.PORT}")

        db_connector = DatabaseConnector("event_system.db")
        self.user_service = UserService(db_connector)
        self.event_service = EventService(db_connector)

    def handle_client(self, client_socket, address):
        """클라이언트 요청 처리"""
        print(f"New connection from {address}")
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                print(f"Received data: {data}")
                response = self.process_request(data)
                client_socket.sendall(response.encode())
        except Exception as e:
            print(f"Error with client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed for {address}")

    def process_request(self, data):
        """클라이언트 요청 처리"""
        try:
            commands = data.split(' ')
            command = commands[0].lower()

            if command == 'register':
                return self.user_service.register_user(*commands[1:])
            elif command == 'login':
                return self.user_service.login(*commands[1:])
            elif command == 'reserve':
                return self.event_service.reserve_ticket(*map(int, commands[1:]))
            elif command == 'cancel':
                return self.event_service.cancel_reservation(*map(int, commands[1:]))
            else:
                return "Unknown command"
        except TypeError:
            return "Error: Invalid arguments"
        except Exception as e:
            print(f"Unexpected error in process_request: {e}")
            return "Error: Request failed"

    def start(self):
        """서버 시작"""
        initialize_database()
        print("Database initialized")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
        except KeyboardInterrupt:
            print("Shutting down server")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    server = EventServer()
    server.start()
