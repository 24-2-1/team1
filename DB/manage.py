import asyncio
from db import initialize_database, AsyncDatabaseConnector


class manage(AsyncDatabaseConnector):
    async def drop_all_tables(self):
        """모든 테이블 삭제"""
        try:
            tables = await self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
                fetch_all=True
            )
            for table in tables:
                table_name = table[0]
                await self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
            print("모든 테이블이 삭제되었습니다.")
        except Exception as e:
            print(f"Error while dropping tables: {e}")

    async def drop_table(self, table_name):
        """특정 테이블 삭제"""
        try:
            # 테이블 존재 여부 확인
            existing_table = await self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?;",
                (table_name,),
                fetch_one=True
            )
            if existing_table:
                await self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                print(f"테이블 '{table_name}'이 삭제되었습니다.")
            else:
                print(f"테이블 '{table_name}'이 존재하지 않습니다.")
        except Exception as e:
            print(f"Error while dropping table '{table_name}': {e}")

    async def create_event(self, name, description, date, available_tickets):
        """이벤트 생성"""
        try:
            # 이미 같은 이름의 이벤트가 존재하는지 확인
            existing_event = await self.execute_query(
                "SELECT name FROM events WHERE name = ?",
                (name,),
                fetch_one=True
            )
            
            if existing_event:
                print(f"이벤트 '{name}'은 이미 존재합니다.")  # 중복 이벤트가 있으면 생성하지 않음
                return
            
            # 이벤트가 존재하지 않으면 새로운 이벤트 생성
            await self.execute_query(
                'INSERT INTO events (name, description, date, available_tickets) VALUES (?, ?, ?, ?)',
                (name, description, date, available_tickets)
            )
            print(f"이벤트 '{name}'이 생성되었습니다.")
            
        except Exception as e:
            print(f"Error while creating event '{name}': {e}")
        
    async def update_event(self, event_id, name=None, description=None, date=None, available_tickets=None):
        """이벤트 내용 수정"""
        try:
            # 수정할 이벤트가 존재하는지 확인
            existing_event = await self.execute_query(
                "SELECT id FROM events WHERE id = ?",
                (event_id,),
                fetch_one=True
            )
            
            if not existing_event:
                print(f"이벤트 ID {event_id}는 존재하지 않습니다.")  # 이벤트가 존재하지 않으면 수정 불가
                return
            
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
            await self.execute_query(query, params)
            print(f"이벤트 ID {event_id}가 성공적으로 수정되었습니다.")
            
        except Exception as e:
            print(f"Error while updating event '{event_id}': {e}")
        
    async def get_event_reservations(self, event_id):
        """특정 이벤트의 예약자 목록 조회"""
        query = '''
        SELECT users.userid
        FROM reservations
        JOIN users ON reservations.user_id = users.userid
        WHERE reservations.event_id = ?
        '''
        reservations = await self.execute_query(query, (event_id,), fetch_all=True)

        if reservations:
            print(f"이벤트 ID {event_id}의 예약자 목록:")
            for user_id in reservations:
                print(f"- 사용자 ID: {user_id}") # (사용자ID:1,)
        else:
            print(f"이벤트 ID {event_id}에 대한 예약자가 없습니다.")

        
class UserInputHandler:
    """사용자로부터 입력을 처리하는 클래스"""
    @staticmethod
    def get_event_data():
        name = input("이벤트 이름: ")
        description = input("이벤트 설명: ")
        date = input("이벤트 날짜 (YYYY-MM-DD): ")
        available_tickets = int(input("사용 가능한 티켓 수: "))
        return name, description, date, available_tickets

    @staticmethod
    def get_event_id():
        return int(input("수정할 이벤트의 ID를 입력하세요: "))

class RequestData(manage):
    """Database 관리 및 입력 데이터 처리"""
    async def create_event_with_input(self):
        event_data = UserInputHandler.get_event_data()
        await self.create_event(*event_data)

    async def update_event_with_input(self):
        event_id = UserInputHandler.get_event_id()
        print("수정할 필드만 입력하고, 생략할 필드는 Enter를 누르세요.")
        name = input("수정할 이름: ") or None
        description = input("수정할 설명: ") or None
        date = input("수정할 날짜 (YYYY-MM-DD): ") or None
        available_tickets = input("수정할 티켓 수: ")
        available_tickets = int(available_tickets) if available_tickets else None
        await self.update_event(event_id, name, description, date, available_tickets)

async def first_data():
    """초기 이벤트 데이터 삽입"""
    connector = AsyncDatabaseConnector()
    async with connector as conn:
        # 이벤트가 이미 존재하는지 확인
        event_count = await connector.execute_query(
            "SELECT COUNT(*) FROM events", fetch_one=True
        )
        
        if event_count and event_count[0] == 0:  # 이벤트 테이블이 비어있는 경우 초기 데이터 삽입
            initial_events = [
                ("웃는남자", "뮤지컬 웃는남자", "2025-01-01", 2),
                ("베르테르", "뮤지컬 베르테르", "2025-01-13", 9),
                ("킹키부츠", "뮤지컬 킹키부츠", "2025-01-31", 9)
            ]
            # 데이터를 한 번에 삽입
            for event in initial_events:
                await connector.execute_query(
                    "INSERT INTO events (name, description, date, available_tickets) VALUES (?, ?, ?, ?)",
                    params=event
                )
            seats= {
                "1": ("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"),
                "2":("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"),
                "3":("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3")
            }
            for event_id, seat_list in seats.items():
                for seat in seat_list:
                    await connector.execute_query(
                        "INSERT INTO seats (event_id, seat_number, status) VALUES (?, ?, ?)",
                        params=(event_id, seat, '예약 가능')  # 기본 상태는 '예약가능'로 설정
                    )
            print("초기 이벤트 데이터가 성공적으로 삽입되었습니다.")




# Main 실행부
if __name__ == "__main__":
    system = RequestData()

    async def main():
        while True:
            await initialize_database()
            await first_data()
            print("0. 종료하기")
            print("1. 모든 테이블 초기화")
            print("2. 특정 테이블의 데이터 초기화")
            print("3. 새로운 이벤트 생성")
            print("4. 이벤트 내용 수정")
            print("5. 이벤트 예약자 목록 조회")

            choice = input("Enter your choice: ")

            if choice == "0":
                break
            elif choice == "1":
                await system.drop_all_tables()
            elif choice == "2":
                table_name = input("삭제할 테이블 이름: ")
                await system.drop_table(table_name)
            elif choice == "3":
                await system.create_event_with_input()
            elif choice == "4":
                await system.update_event_with_input()
            elif choice == "5":
                event_id = int(input("예약자 목록을 확인할 이벤트 ID: "))
                await system.get_event_reservations(event_id)
            else:
                print("올바른 번호를 입력하세요.")

    asyncio.run(main())

