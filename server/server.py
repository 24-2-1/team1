import sqlite3
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from db import initialize_database
import threading

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
class Event(EventSystem):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()

    def log_action(self, action, user_id=None, event_id=None):
        """로그를 기록"""
        self.execute_query(
            'INSERT INTO logs (action, user_id, event_id) VALUES (?, ?, ?)',
            (action, user_id, event_id)
        )

    def register_user(self, username, password):
        """사용자 등록"""
        try:
            self.execute_query(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            print(f"사용자 {username}가 성공적으로 등록되었습니다.")
        except sqlite3.IntegrityError:
            print(f"사용자 이름 {username}이 이미 존재합니다.")

    def login(self, username, password):
        """로그인 기능"""
        user = self.execute_query(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, password),
            fetch_one=True
        )
        if user:
            print(f"로그인 성공! 사용자 ID: {user[0]}")
            return user[0]
        else:
            print("로그인 실패! 사용자 이름 또는 비밀번호가 틀렸습니다.")
            return None

    def reserve_ticket(self, user_id, event_id):
        """티켓 예약 및 대기자 등록"""
        with self.lock:
            try:
                available_tickets = self.execute_query(
                    'SELECT available_tickets FROM events WHERE id = ?',
                    (event_id,),
                    fetch_one=True
                )

                if available_tickets and available_tickets[0] > 0:
                    # 예약 처리
                    self.execute_query(
                        'INSERT INTO reservations (user_id, event_id) VALUES (?, ?)',
                        (user_id, event_id)
                    )
                    self.execute_query(
                        'UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?',
                        (event_id,)
                    )
                    print(f"User {user_id} successfully reserved a ticket for event {event_id}.")
                    self.log_action("reserve", user_id, event_id)
                elif available_tickets:
                    # 대기자 등록
                    self.execute_query(
                        'INSERT INTO waitlist (user_id, event_id) VALUES (?, ?)',
                        (user_id, event_id)
                    )
                    print(f"User {user_id} added to waitlist for event {event_id}.")
                    self.log_action("waitlist", user_id, event_id)
                else:
                    print(f"Event {event_id} does not exist.")
            except Exception as e:
                print(f"Error: {e}")

    def cancel_reservation(self, user_id, event_id):
        """예약 취소 및 대기자 처리"""
        try:
            self.execute_query(
                'DELETE FROM reservations WHERE user_id = ? AND event_id = ?',
                (user_id, event_id)
            )

            # 대기자 처리
            next_user = self.execute_query(
                'SELECT user_id FROM waitlist WHERE event_id = ? ORDER BY id LIMIT 1',
                (event_id,),
                fetch_one=True
            )
            if next_user:
                self.execute_query(
                    'INSERT INTO reservations (user_id, event_id) VALUES (?, ?)',
                    (next_user[0], event_id)
                )
                self.execute_query(
                    'DELETE FROM waitlist WHERE user_id = ? AND event_id = ?',
                    (next_user[0], event_id)
                )
                print(f"User {next_user[0]} moved from waitlist to reservation for event {event_id}.")
                self.log_action("reserve_from_waitlist", next_user[0], event_id)
            else:
                self.execute_query(
                'UPDATE events SET available_tickets = available_tickets + 1 WHERE id = ?',
                (event_id,)
            )
            print(f"Reservation for User {user_id} canceled for event {event_id}.")
            self.log_action("cancel", user_id, event_id)
        except Exception as e:
            print(f"Error: {e}")

    def view_logs(self):
        """로그 조회"""
        logs = self.execute_query('SELECT * FROM logs', fetch_all=True)
        print("Logs:")
        for log in logs:
            print(log)

# 실행 흐름
if __name__ == "__main__":
    initialize_database()
    system = Event()

    # 사용자 등록 및 로그인
    system.register_user("john_doe", "password123")
    user_id = system.login("john_doe", "password123")

    # 이벤트 예약
    if user_id:
        system.reserve_ticket(user_id, 1)

    # 로그 조회
    system.view_logs()
