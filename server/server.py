import socket
import threading
import sqlite3
import os
import sys

# DB 초기화 모듈 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db import initialize_database


class EventSystem:
    def __init__(self, db_name="event_system.db"):
        self.db_name = db_name

    def connect(self):
        """DB 연결 컨텍스트 매니저"""
        return sqlite3.connect(self.db_name)

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """쿼리 실행 및 결과 반환"""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            conn.commit()


class EventServer(EventSystem):
    HOST = '0.0.0.0'
    PORT = 5000
    MAX_CONNECTIONS = 5

    def __init__(self):
        super().__init__()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.HOST, self.PORT))
        self.server_socket.listen(self.MAX_CONNECTIONS)
        print(f"Server started on {self.HOST}:{self.PORT}")

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
                return self.register_user(*commands[1:])
            elif command == 'login':
                return self.login(*commands[1:])
            elif command == 'reserve':
                return self.reserve_ticket(*map(int, commands[1:]))
            elif command == 'cancel':
                return self.cancel_reservation(*map(int, commands[1:]))
            elif command == 'logs':
                return self.view_logs()
            else:
                return "Unknown command"
        except TypeError:
            return "Error: Invalid arguments"
        except Exception as e:
            print(f"Unexpected error in process_request: {e}")
            return "Error: Request failed"

    def register_user(self, username, password):
        """사용자 등록"""
        try:
            if self.execute_query('SELECT 1 FROM users WHERE username = ?', (username,), fetch_one=True):
                return f"Error: Username {username} already exists"
            self.execute_query('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            return f"User {username} registered successfully"
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return "Error: Registration failed"

    def login(self, username, password):
        """로그인"""
        try:
            user = self.execute_query(
                "SELECT id FROM users WHERE username = ? AND password = ?",
                (username, password),
                fetch_one=True
            )
            return f"Login successful! User ID: {user[0]}" if user else "Error: Invalid username or password"
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return "Error: Login failed"

    def reserve_ticket(self, user_id, event_id):
        """티켓 예약"""
        try:
            available_tickets = self.execute_query(
                'SELECT available_tickets FROM events WHERE id = ?',
                (event_id,),
                fetch_one=True
            )

            if not available_tickets:
                return f"Error: Event {event_id} does not exist"
            if available_tickets[0] <= 0:
                return f"Error: No available tickets for event {event_id}"

            self.execute_query('INSERT INTO reservations (user_id, event_id) VALUES (?, ?)', (user_id, event_id))
            self.execute_query('UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?', (event_id,))
            return f"User {user_id} reserved a ticket for event {event_id}"
        except Exception as e:
            print(f"Unexpected error during reservation: {e}")
            return "Error: Reservation failed"

    def cancel_reservation(self, user_id, event_id):
        """예약 취소"""
        try:
            self.execute_query('DELETE FROM reservations WHERE user_id = ? AND event_id = ?', (user_id, event_id))
            self.execute_query('UPDATE events SET available_tickets = available_tickets + 1 WHERE id = ?', (event_id,))
            return f"Reservation canceled for User {user_id} on Event {event_id}"
        except Exception as e:
            print(f"Unexpected error during cancellation: {e}")
            return "Error: Cancellation failed"

    def view_logs(self):
        """로그 조회"""
        try:
            logs = self.execute_query('SELECT * FROM logs', fetch_all=True)
            return "\n".join([str(log) for log in logs])
        except Exception as e:
            print(f"Unexpected error during log retrieval: {e}")
            return "Error: Log retrieval failed"

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
