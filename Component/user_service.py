from DB.db import AsyncDatabaseConnector
from .event_service import log_action
class AsyncUserService:
    def __init__(self, db_connector: AsyncDatabaseConnector,clients):
        self.db_connector = db_connector
        self.clients = clients

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
            await log_action(self.db_connector,userid, "회원가입 성공")
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
            return "로그인 실패"
    
    def logout(self,user_id):
        """로그아웃 요청 처리"""
        if user_id in self.clients:
            del self.clients[user_id]
        return f"{user_id}님이 로그아웃 하셨습니다."

    




