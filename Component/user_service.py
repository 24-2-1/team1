from DB.db import AsyncDatabaseConnector
from .event_service import log_action
class AsyncUserService:
    def __init__(self, db_connector: AsyncDatabaseConnector):
        self.db_connector = db_connector

    async def register_user(self, userid, password):
        """사용자 등록"""
        try:
            existing_user = await self.db_connector.execute_query(
                'SELECT 1 FROM users WHERE userid = ?', (userid,), fetch_one=True
            )
            if existing_user:
                return f"Error: Username '{userid}' already exists"
            
            await self.db_connector.execute_query( 
                'INSERT INTO users (userid, password) VALUES (?, ?)', (userid, password)
            )
            
            # 사용자 등록 로그 기록
            await log_action(self.db_connector,userid, "User registered successfully")
            return f"User '{userid}' registered successfully"
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return "Error: Registration failed"

    async def login(self, userid, password):
        """로그인"""
        try:
            user = await self.db_connector.execute_query(
                "SELECT userid FROM users WHERE userid = ? AND password = ?",
                (userid, password),
                fetch_one=True
            )
            
            if user:
                # 로그인 성공 로그 기록
                await log_action(self.db_connector, userid, "로그인 성공")
                return user[0]
            else:
                return "로그인 실패"
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return "Error: Login failed"
    



