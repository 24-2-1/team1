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

                return f"Reservation canceled for User {user_id} on Event {event_id}"
