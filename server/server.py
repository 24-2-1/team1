import socket
from concurrent.futures import ThreadPoolExecutor
from db import initialize_database, DatabaseConnector
from user_service import UserService
from event_service import EventService

class LimitedServer:
    def __init__(self, host='127.0.0.1', port=5000, max_connections=2):
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_connections)
        self.executor = ThreadPoolExecutor(max_workers=max_connections)
        db_connector = DatabaseConnector("event_system.db")
        self.user_service = UserService(db_connector)
        self.event_service = EventService(db_connector)
        print(f"Server started on {self.host}:{self.port} with max {self.max_connections} connections")

    def handle_client(self, client_socket, address):
        """클라이언트 요청 처리"""
        try:
            print(f"Connected: {address}")
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                response = self.process_request(data)
                client_socket.sendall(response.encode())
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed: {address}")

    def start(self):
        """서버 시작"""
        initialize_database()
        print("Database initialized")
        try:
            while True:
                try:
                    client_socket, addr = self.server_socket.accept()
                    self.executor.submit(self.handle_client, client_socket, addr)
                except socket.error as e:
                    print(f"Connection refused or failed: {e}")
        except KeyboardInterrupt:
            print("Server shutting down")
        finally:
            self.server_socket.close()
    
    def process_request(self, data):
        """클라이언트 요청 처리"""
        try:
            commands = data.split(' ')
            command = commands[0].lower()

            command_map = {
            'register': lambda args: self.user_service.register_user(*args),
            'login': lambda args: self.user_service.login(*args),
            'reserve': lambda args: self.event_service.reserve_ticket(*map(int, args)),
            'cancel': lambda args: self.event_service.cancel_reservation(*map(int, args))
        }

            if command in command_map:
                return command_map[command](commands[1:])
            else:
                return "Unknown command"
        except TypeError:
            return "Error: Invalid arguments"
        except Exception as e:
            print(f"Unexpected error in process_request: {e}")
            return "Error: Request failed"

if __name__ == "__main__":
    server = LimitedServer(max_connections=5)
    server.start()