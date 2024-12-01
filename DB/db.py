import aiosqlite
import asyncio
import os

class AsyncDatabaseConnector:
    def __init__(self, db_name="event_system.db"):
        # server 디렉토리의 절대경로를 기준으로 데이터베이스 파일 경로 설정
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        self.connection = None

    async def connect(self):
        """데이터베이스 연결"""
        if not self.connection:
            self.connection = await aiosqlite.connect(self.db_path)
        return self.connection

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        if not self.connection:
            self.connection = await aiosqlite.connect(self.db_path)
        return self.connection

    async def __aexit__(self, exc_type, exc_value, traceback):
        """비동기 컨텍스트 매니저 종료"""
        if self.connection:
            await self.connection.close()
            self.connection = None

    async def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """쿼리 실행 및 결과 반환"""
        try:
            print(f"Executing query: {query} with params: {params}")  # 디버깅 로그
            async with self.connect() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params or [])
                    if fetch_one:
                        return await cursor.fetchone()
                        print(f"Query fetch_one result: {result}")  # 디버깅 로그
                        return result
                    if fetch_all:
                        result = await cursor.fetchall()
                        print(f"Query fetch_all result: {result}")  # 디버깅 로그
                        return await cursor.fetchall()
                    await conn.commit()
                    print("Commit successful")  # 디버깅 로그
        except Exception as e:
            print(f"Error executing query: {e}")

# 데이터베이스 초기화 함수
    async def initialize_database():
        """데이터베이스 초기화"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "event_system.db")

        connector = AsyncDatabaseConnector(db_name=db_path)
        async with connector as conn:
            async with conn.cursor() as cursor:
            # 테이블 생성
                tasks = [
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
                '''),
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    available_tickets INTEGER NOT NULL
                )
                '''),
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )
                '''),
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS waitlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )
                '''),
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    user_id INTEGER,
                    event_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                ''')
            ]

            # 병렬 실행
            await asyncio.gather(*tasks)

            # 기존 데이터 삭제 및 ID 초기화
            await cursor.execute("DELETE FROM events")
            await cursor.execute("DELETE FROM sqlite_sequence WHERE name='events'")

            # 초기 데이터 삽입
            initial_events = [
                ("웃는남자", "뮤지컬 웃는남자", "2025-01-01", 100),
                ("베르테르", "뮤지컬 베르테르", "2025-01-13", 80),
                ("킹키부츠", "뮤지컬 킹키부츠", "2025-01-31", 120)
            ]
            await cursor.executemany(
                "INSERT INTO events (name, description, date, available_tickets) VALUES (?, ?, ?, ?)",
                initial_events
            )

            await conn.commit()

