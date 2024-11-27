from db import initialize_database,DatabaseConnector

class add_test(DatabaseConnector):
    def drop_all_tables(self):
        """모든 테이블 삭제"""
        try:
            tables = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
                fetch_all=True
            )
            for table in tables:
                table_name = table[0]
                self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
            print("모든 테이블이 삭제되었습니다.")
        except Exception as e:
            print(f"Error while dropping tables: {e}")

    def all_delete(self):
        """모든 테이블의 데이터 삭제"""
        try:
            tables = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
                fetch_all=True
            )
            for table in tables:
                table_name = table[0]
                self.execute_query(f"DELETE FROM {table_name}")
                print(f"테이블 {table_name}의 모든 데이터가 삭제되었습니다.")
            print("모든 데이터가 삭제되었습니다.")
        except Exception as e:
            print(f"Error while deleting all data: {e}")
    def drop_table(self, table_name):
        """특정 테이블 삭제"""
        try:
            # 테이블 존재 여부 확인
            existing_table = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?;",
                (table_name,),
                fetch_one=True
            )
            if existing_table:
                self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                print(f"테이블 '{table_name}'이 삭제되었습니다.")
            else:
                print(f"테이블 '{table_name}'이 존재하지 않습니다.")
        except Exception as e:
            print(f"Error while dropping table '{table_name}': {e}")

    def create_event(self, name, description, date, available_tickets):
        """이벤트 생성"""
        self.execute_query(
            'INSERT INTO events (name, description, date, available_tickets) VALUES (?, ?, ?, ?)',
            (name, description, date, available_tickets)
        )
        print(f"이벤트 '{name}'이 생성되었습니다.")
        
    def update_event(self, event_id, name=None, description=None, date=None, available_tickets=None):
        """이벤트 내용 수정"""
        fields = []
        params = []

        if name:
            fields.append("name = ?")
            params.append(name)
        if description:
            fields.append("description = ?")
            params.append(description)
        if date:
            fields.append("date = ?")
            params.append(date)
        if available_tickets is not None:
            fields.append("available_tickets = ?")
            params.append(available_tickets)

        if not fields:
            raise ValueError("수정할 내용이 제공되지 않았습니다.")

        # Update query 구성
        params.append(event_id)
        query = f"UPDATE events SET {', '.join(fields)} WHERE id = ?"
        self.execute_query(query, params)
        print(f"이벤트 ID {event_id}가 성공적으로 수정되었습니다.")
        
    def get_event_reservations(self, event_id):
        """특정 이벤트의 예약자 목록 조회"""
        query = '''
        SELECT users.id, users.username
        FROM reservations
        JOIN users ON reservations.user_id = users.id
        WHERE reservations.event_id = ?
        '''
        reservations = self.execute_query(query, (event_id,), fetch_all=True)

        if reservations:
            print(f"이벤트 ID {event_id}의 예약자 목록:")
            for user_id, username in reservations:
                print(f"- 사용자 ID: {user_id}, 사용자명: {username}")
        else:
            print(f"이벤트 ID {event_id}에 대한 예약자가 없습니다.")

        
        
if __name__ == "__main__":
    initialize_database()
    system = add_test()
    system.create_event("Tech Conference", "A conference about tech.", "2024-12-01", 1)
    
    # system.drop_all_tables()
    system.update_event(
        event_id=1,
        description="pabc",
        date="2024-12-25",
        available_tickets=100
    )
    
    
