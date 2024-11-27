import sqlite3
import os

class DatabaseConnector:
    def __init__(self, db_name="event_system.db"):
        # server 디렉토리의 절대경로를 기준으로 데이터베이스 파일 경로 설정
        server_dir = os.path.dirname(os.path.abspath(__file__))  # db.py의 위치
        self.db_path = os.path.join(server_dir, db_name)  # server/event_system.db로 절대경로 생성

    def connect(self):
        """데이터베이스 연결"""
        return sqlite3.connect(self.db_path)

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
            

# 데이터베이스 초기화
def initialize_database():
    """데이터베이스 초기화"""
    # db.py가 있는 디렉토리의 event_system.db에 대한 경로 설정
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "event_system.db")

    connector = DatabaseConnector(db_name=db_path)
    with connector.connect() as conn:
        cursor = conn.cursor()

        # 사용자 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        ''')

        # 이벤트 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            available_tickets INTEGER NOT NULL
        )
        ''')

        # 예약 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
        ''')

        # 대기자 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
        ''')

        # 로그 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            user_id INTEGER,
            event_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()

