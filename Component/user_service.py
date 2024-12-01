class AsyncUserService:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    async def register_user(self, username, password):
        """사용자 등록"""
        try:
            print(f"Attempting to register user: {username}")  # 디버깅 로그
            existing_user = await self.db_connector.execute_query(
                'SELECT 1 FROM users WHERE username = ?', (username,), fetch_one=True
            )
            print(f"Existing user: {existing_user}")  # 디버깅 로그
            if existing_user:
                return f"Error: Username {username} already exists"
            
            await self.db_connector.execute_query(
                'INSERT INTO users (username, password) VALUES (?, ?)', (username, password)
            )
            print(f"User {username} registered successfully")  # 디버깅 로그
            return f"User {username} registered successfully"
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return "Error: Registration failed"

    async def login(self, username, password):
        """로그인"""
        try:
            print(f"Attempting login with username: {username} and password: {password}")  # 디버깅 로그
            user = await self.db_connector.execute_query(
                "SELECT id FROM users WHERE username = ? AND password = ?",
                (username, password),
                fetch_one=True
            )
            print(f"Query result for user: {user}")  # 디버깅 로그
            return f"Login successful! User ID: {user[0]}" if user else "Error: Invalid username or password"
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return "Error: Login failed"
