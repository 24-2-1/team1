from DB.db import AsyncDatabaseConnector
from .event_service import log_action

class AsyncUserService:
    def __init__(self, db_connector: AsyncDatabaseConnector):
        self.db_connector = db_connector

    async def register_user(self, username, password):
        """사용자 등록"""
        try:
            existing_user = await self.db_connector.execute_query(
                'SELECT 1 FROM users WHERE username = ?', (username,), fetch_one=True
            )
            if existing_user:
                return f"Error: Username '{username}' already exists"
            
            await self.db_connector.execute_query(
                'INSERT INTO users (username, password) VALUES (?, ?)', (username, password)
            )
            
            # 사용자 등록 로그 기록
            await log_action(self.db_connector, username, "User registered successfully")
            return f"User '{username}' registered successfully"
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return "Error: Registration failed"

    async def login(self, username, password):
        """로그인"""
        try:
            user = await self.db_connector.execute_query(
                "SELECT id FROM users WHERE username = ? AND password = ?",
                (username, password),
                fetch_one=True
            )
            
            if user:
                # 로그인 성공 로그 기록
                await log_action(self.db_connector, username, "Login successful")
                return f"Login successful! User ID: {user[0]}"
            else:
                return "Error: Invalid username or password"
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return "Error: Login failed"



