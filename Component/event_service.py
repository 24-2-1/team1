import asyncio
from DB.db import AsyncDatabaseConnector  # AsyncDatabaseConnector 클래스 import
import logging

class AsyncEventService:
    def __init__(self, db_connector: AsyncDatabaseConnector, clients):
        self.db_connector = db_connector
        self.locks = {}
        self.locks_lock = asyncio.Lock()
        self.clients = clients

    async def get_event_lock(self, event_id):
        """이벤트 ID별 비동기 락 반환"""
        async with self.locks_lock:
            if event_id not in self.locks:
                self.locks[event_id] = asyncio.Lock()
            return self.locks[event_id]
    
    async def reserve_ticket(self, user_id, event_id, seat_number=None):
        """티켓 예약"""
        event_lock = await self.get_event_lock(event_id)
        async with event_lock:
            # 좌석 번호가 입력되지 않으면 좌석을 예약할 수 없다.
            if not seat_number:
                return f"좌석을 선택 안했어 다시 해"
            
            available_tickets = await self.db_connector.execute_query(
                "SELECT available_tickets FROM events WHERE id = ?", 
                params=(event_id,), 
                fetch_one=True
            )
            if not available_tickets or available_tickets[0] <= 0:
                await self.db_connector.execute_query(
                "INSERT INTO waitlist (user_id, event_id) VALUES (?, ?)", 
                params=(user_id, event_id)
            )
                return f" {event_id} 대기자로 갔어"

            seat_exists = await self.db_connector.execute_query(
                "SELECT status FROM seats WHERE event_id = ? AND seat_number = ?",
                params=(event_id, seat_number),
                fetch_one=True
            )
            logging.debug(f"[cancel_reservation] 빈좌석확인: {seat_exists}")

            if seat_exists[0] == '예약 불가능':
                return f"{seat_number} 자리는 예약돼있어"

            # 예약 처리
            await self.db_connector.execute_query( # 예약
                "INSERT INTO reservations (user_id, event_id,seat_number) VALUES (?, ?, ?)", 
                params=(user_id, event_id, seat_number)
            )
            #좌석 예약 불가능 변경
            await self.db_connector.execute_query( 
                "UPDATE seats SET status = '예약 불가능' WHERE event_id = ? AND seat_number = ?", 
                params=(event_id,seat_number)
            )
            await self.db_connector.execute_query(
                "UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?", 
                params=(event_id,)
            )
            
            # 로그 기록
            try:
                await log_action(self.db_connector, user_id, f"티켓 예약 성공 {event_id}", event_id)
            except Exception as e:
                return f"티켓 예약 최고 에러"
        
    async def cancel_reservation(self, user_id, event_id):
        """예약 취소"""
        event_lock = await self.get_event_lock(event_id)
        async with event_lock:
            reservation_exists = await self.db_connector.execute_query(
                "SELECT id, seat_number FROM reservations WHERE user_id = ? AND event_id = ?",
                params=(user_id, event_id),
                fetch_one=True
            )
            id_exists,seat = reservation_exists
            if not id_exists:
                return f"No reservation found for user {user_id} on event {event_id}."
            else:
                await self.db_connector.execute_query(
                "UPDATE seats SET status = '예약 가능' WHERE event_id = ? AND seat_number = ?",
                params=(event_id, seat)
            )
            # 예약 취소 처리
            await self.db_connector.execute_query(
                "DELETE FROM reservations WHERE user_id = ? AND event_id = ?",
                params=(user_id, event_id)
            )
            await self.db_connector.execute_query(
                "UPDATE events SET available_tickets = available_tickets + 1 WHERE id = ?",
                params=(event_id,)
            )

            available_tickets = await self.db_connector.execute_query(
                "SELECT available_tickets FROM events WHERE id = ?",
                params=(event_id,),
                fetch_one=True
            )
            logging.debug(f"[cancel_reservation] after wait: {available_tickets[0]}")

            if available_tickets and available_tickets[0] > 0:
                await self.handle_waitlist(event_id,seat)

            return f"Reservation canceled for user {user_id} on event {event_id}"

        
    async def handle_waitlist(self, event_id,seat_number):
        """대기자 목록 처리"""
        try:
            # 대기자 조회
            logging.debug(f"[cancel_reservation] handle: {seat_number}")

            waitlist_user = await self.db_connector.execute_query(
                "SELECT user_id FROM waitlist WHERE event_id = ? ORDER BY id ASC LIMIT 1",
                params=(event_id,),
                fetch_one=True
            )
            if not waitlist_user:
                print(f"No waitlist user found for event {event_id}.")
                return  # 대기자가 없으면 종료

            waitlist_user_id = waitlist_user[0]
            # event 이름 조회
            event_name = await self.db_connector.execute_query( 
                "SELECT name FROM events WHERE id = ?",
                params=(event_id,),
                fetch_one=True
            )
            #예약을 다시 하니까 좌석 불가능으로
            await self.db_connector.execute_query(
                "UPDATE seats SET status = '예약 불가능' WHERE event_id = ? AND seat_number = ?",
                params=(event_id, seat_number)
            )
            logging.debug(f"[cancel_reservation] 대기자: {waitlist_user_id}")
            #대기자를 예약자에 추가
            await self.db_connector.execute_query( 
                "INSERT INTO reservations (user_id, event_id,seat_number) VALUES (?, ?, ?)", 
                params=(waitlist_user_id, event_id, seat_number)
            )
            #현재 티켓 개수 다시 줄이기
            await self.db_connector.execute_query( 
                "UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?",
                params=(event_id,)
            )
            logging.debug(f"[cancel_reservation] 온라인: {self.clients}")
            # 클라이언트 연결 상태 확인
            if waitlist_user_id in self.clients:
                target_writer = self.clients[waitlist_user_id]
                message = f" {event_name} 앞 사람이 취소해서 자동 예약됐어."
                try:
                    target_writer.write(message.encode('utf-8'))
                    await target_writer.drain()
                except Exception as e:
                    return f"handle 실패"

            # 대기자 목록에서 삭제
            await self.db_connector.execute_query(
                "DELETE FROM waitlist WHERE user_id = ? AND event_id = ?",
                params=(waitlist_user_id, event_id)
            )

            # 로그 기록
            await log_action(self.db_connector, waitlist_user_id, f"{event_id} 예약했음", event_id)
        except Exception as e:
            print(f"Error in handle_waitlist: {e}")
            raise  # 디버깅을 위해 예외 재발생

    async def get_seat_availability(self, event_id):
        """이벤트의 좌석 상태 조회"""
        # 해당 이벤트의 좌석을 가져옴
        seats = await self.db_connector.execute_query(
            "SELECT seat_number, status FROM seats WHERE event_id = ?",
            params=(event_id,),
            fetch_all=True
        )

        if not seats:
            return f"Event {event_id} not found or no seats available."
        
        # 좌석을 2D 배열로 그룹화하기 위해 행렬 크기 설정 (예시: 3x3)
        rows = 3  # 행의 수
        cols = 3  # 열의 수
        seat_matrix = [['' for _ in range(cols)] for _ in range(rows)]  # 2D 배열 초기화

        # 좌석 번호를 행렬에 배치
        for seat in seats:
            seat_number = seat[0]  # 좌석 번호 (예: C1, C2, C3)
            status = seat[1]  # 좌석 상태 (예: "available", "reserved")
            
            try:
                # 좌석 번호에서 행, 열 추출
                row = int(seat_number[1]) - 1  # C1 -> row 0, C2 -> row 1, etc.
                col = ord(seat_number[0]) - ord('A')  # A -> column 0, B -> column 1, etc.
                
                # 좌석 상태 업데이트
                seat_matrix[row][col] = f"{seat_number}({status})"
            except Exception as e:
                print(f"Error extracting row/column for seat {seat_number}: {e}")
                # 오류가 발생하면 해당 좌석을 건너뛰고 계속 진행
                return f"좌석현황에러"

        # 좌석을 2D 배열 형식으로 포맷팅하여 출력
        seat_info = ""
        for row in seat_matrix:
            seat_info += " | ".join([seat if seat else "Empty" for seat in row]) + "\n"

        return f"Event {event_id} Seat Availability:\n{seat_info}"    
            
    async def get_all_events(self):
        """모든 이벤트 조회"""
        events = await self.db_connector.execute_query(
            "SELECT * FROM events", 
            fetch_all=True
        )
        if events:
            # 이벤트를 문자열로 변환하여 반환
            events_list = "\n".join(
                f"ID: {event[0]}, Name: {event[1]}, Description: {event[2]}, Date: {event[3]}, Available Tickets: {event[4]}"
                for event in events
            )
            return events_list  # 이제 문자열로 반환
        return "No events available."

    async def get_user_logs(self, user_id):
        """사용자의 로그 기록 조회"""
        logs = await self.db_connector.execute_query(
            "SELECT action, timestamp FROM logs WHERE user_id = ? ORDER BY timestamp DESC", 
            params=(user_id,), 
            fetch_all=True
        )
        if logs:
            logs_list = "\n".join(
                f"Action: {log[0]}, Timestamp: {log[1]}" for log in logs
            )
            return logs_list
        return "No logs found for this user."
    
async def log_action(db_connector: AsyncDatabaseConnector, user_id, action, event_id=None):
    """사용자 활동 로그 기록"""
    try:
        if event_id:
            # event_id가 제공된 경우
            await db_connector.execute_query(
                "INSERT INTO logs (user_id, action, event_id, timestamp) VALUES (?, ?, ?, datetime('now'))",
                params=(user_id, action, event_id),
            )
        else:
            # event_id가 제공되지 않은 경우
            await db_connector.execute_query(
                "INSERT INTO logs (user_id, action, timestamp) VALUES (?, ?, datetime('now'))",
                params=(user_id, action),
            )
        print(f"Action logged for {user_id}: {action}, Event ID: {event_id if event_id else 'N/A'}")
    except Exception as e:
        print(f"Error logging action: {e}")
