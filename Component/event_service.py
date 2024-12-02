import asyncio
from DB.db import AsyncDatabaseConnector  # AsyncDatabaseConnector 클래스 import

class AsyncEventService:
    def __init__(self, db_connector: AsyncDatabaseConnector):
        self.db_connector = db_connector
        self.locks = {}
        self.locks_lock = asyncio.Lock()

    async def get_event_lock(self, event_id):
        """이벤트 ID별 비동기 락 반환"""
        async with self.locks_lock:
            if event_id not in self.locks:
                self.locks[event_id] = asyncio.Lock()
            return self.locks[event_id]

    async def log_activity(self, user_id, message):
        """사용자 활동 로그 기록"""
        async with self.db_connector.connect() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO logs (user_id, message) VALUES (?, ?)", (user_id, message)
                )
                await conn.commit()

    async def notify_user_logs(self, user_id):
        """사용자 활동 로그 알림"""
        async with self.db_connector.connect() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT message, timestamp FROM logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
                    (user_id,)
                )
                logs = await cursor.fetchall()
                if logs:
                    print("📋 Recent Activity Logs:")
                    for log in logs:
                        print(f"- {log[1]}: {log[0]}")
                else:
                    print("📋 No recent activity logs found.")

    async def reserve_ticket(self, user_id, event_id):
        """티켓 예약"""
        event_lock = await self.get_event_lock(event_id)
        async with event_lock:
            available_tickets = await self.db_connector.execute_query(
                "SELECT available_tickets FROM events WHERE id = ?", 
                params=(event_id,), 
                fetch_one=True
            )
            if not available_tickets or available_tickets[0] <= 0:
                return f"Error: No tickets available for event {event_id}"

            # 예약 처리
            await self.db_connector.execute_query(
                "INSERT INTO reservations (user_id, event_id) VALUES (?, ?)", 
                params=(user_id, event_id)
            )
            await self.db_connector.execute_query(
                "UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?", 
                params=(event_id,)
            )
            
            # 로그 기록
            await self.log_action(user_id, f"Reserved ticket for event {event_id}")
            
            return f"User {user_id} reserved a ticket for event {event_id}"
    
    async def cancel_reservation(self, user_id, event_id):
        """예약 취소"""
        event_lock = await self.get_event_lock(event_id)
        async with event_lock:
            reservation_exists = await self.db_connector.execute_query(
                "SELECT id FROM reservations WHERE user_id = ? AND event_id = ?", 
                params=(user_id, event_id), 
                fetch_one=True
            )
            if not reservation_exists:
                return f"Error: Reservation does not exist for user {user_id} and event {event_id}"

            # 예약 취소 처리
            await self.db_connector.execute_query(
                "DELETE FROM reservations WHERE user_id = ? AND event_id = ?", 
                params=(user_id, event_id)
            )
            await self.db_connector.execute_query(
                "UPDATE events SET available_tickets = available_tickets + 1 WHERE id = ?", 
                params=(event_id,)
            )
            
            # 로그 기록
            await self.log_action(user_id, f"Canceled reservation for event {event_id}")

            return f"Reservation canceled for User {user_id} on Event {event_id}"

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
    
async def log_action(db_connector: AsyncDatabaseConnector, user_id, action):
    """사용자 활동 로그 기록"""
    await db_connector.execute_query(
        "INSERT INTO logs (user_id, action, timestamp) VALUES (?, ?, datetime('now'))", 
        params=(user_id, action)
    )
