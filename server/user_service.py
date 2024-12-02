class UserService:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def register_user(self, username, password):
        """사용자 등록"""
        try:
            if self.db_connector.execute_query(
                'SELECT 1 FROM users WHERE username = ?', (username,), fetch_one=True
            ):
                return f"Error: Username {username} already exists"
            self.db_connector.execute_query(
                'INSERT INTO users (username, password) VALUES (?, ?)', (username, password)
            )
            return f"User {username} registered successfully"
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return "Error: Registration failed"

    def login(self, username, password):
        """로그인"""
        try:
            user = self.db_connector.execute_query(
                "SELECT id FROM users WHERE username = ? AND password = ?",
                (username, password),
                fetch_one=True
            )
            return f"Login successful! User ID: {user[0]}" if user else "Error: Invalid username or password"
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return "Error: Login failed"
