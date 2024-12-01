import asyncio

class AsyncEventService:
    def __init__(self, db_connector):
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
            async with self.db_connector.connect() as conn:
                async with conn.cursor() as cursor:
                    # 티켓 수량 확인 및 잠금
                    await cursor.execute(
                        "SELECT available_tickets FROM events WHERE id = ? FOR UPDATE", (event_id,)
                    )
                    result = await cursor.fetchone()
                    if not result or result[0] <= 0:
                        return f"Error: No tickets available for event {event_id}"

                    # 티켓 예약
                    await cursor.execute(
                        "INSERT INTO reservations (user_id, event_id) VALUES (?, ?)", (user_id, event_id)
                    )
                    # 티켓 수 감소
                    await cursor.execute(
                        "UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?", (event_id,)
                    )
                    await conn.commit()

                # Log activity
                await self.log_activity(user_id, f"Reserved a ticket for event {event_id}")
                return f"User {user_id} reserved a ticket for event {event_id}"

    async def cancel_reservation(self, user_id, event_id):
        """예약 취소"""
        event_lock = await self.get_event_lock(event_id)
        async with event_lock:
            async with self.db_connector.connect() as conn:
                async with conn.cursor() as cursor:
                    # 예약 취소
                    await cursor.execute(
                        "DELETE FROM reservations WHERE user_id = ? AND event_id = ?", (user_id, event_id)
                    )
                    # 티켓 수 증가
                    await cursor.execute(
                        "UPDATE events SET available_tickets = available_tickets + 1 WHERE id = ?", (event_id,)
                    )
                    await conn.commit()

                # Log activity
                await self.log_activity(user_id, f"Canceled reservation for event {event_id}")
                return f"Reservation canceled for User {user_id} on Event {event_id}"


    async def get_all_events(self):
        """모든 이벤트 조회"""
        async with self.db_connector as conn:  # 수정된 컨텍스트 매니저 사용
            async with conn.cursor() as cursor:
                # 모든 이벤트 조회
                await cursor.execute("SELECT id, name, description, date, available_tickets FROM events")
                events = await cursor.fetchall()
                if events:
                    return "\n".join(
                        f"ID: {event[0]}, Name: {event[1]}, Description: {event[2]}, Date: {event[3]}, Tickets: {event[4]}"
                        for event in events
                    )
                return "No events available."