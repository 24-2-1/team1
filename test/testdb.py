import aiosqlite
import asyncio
import os
class AsyncDatabaseConnector:
    def __init__(self, db_name="database.db"):
        # server 디렉토리의 절대경로를 기준으로 데이터베이스 파일 경로 설정
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        self.connection = None
    async def connect(self):
        if not self.connection:
            self.connection = await aiosqlite.connect(self.db_path)
        return self.connection
    async def __aenter__(self):
        self.connection = await self.connect()
        return self.connection
    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.connection:
            await self.connection.close()
            
    async def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """쿼리 실행 및 결과 반환"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params or [])
                    if fetch_one:
                        return await cursor.fetchone()
                    if fetch_all:
                        return await cursor.fetchall()
                    await conn.commit()
        except Exception as e:
            print(f"Error executing query: {e}")
# 데이터베이스 초기화
async def initialize_database():
    """데이터베이스 초기화"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "database.db")
    connector = AsyncDatabaseConnector(db_name=db_path)
    async with connector as conn:
        async with conn.cursor() as cursor:
            # 병렬로 쿼리 실행
            tasks = [
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userid TEXT UNIQUE NOT NULL,
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
                    event_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
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
            
            # 병렬 실행 및 완료 대기
            await asyncio.gather(*tasks)
            await conn.commit()