import asyncio
from DB.db import AsyncDatabaseConnector
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

class AsyncEventService:
    """이벤트 서비스 클래스"""
    def __init__(self, db_connector, clients):
        self.db_connector = db_connector
        self.clients = clients
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
        try:
            lock = await self.get_event_lock(event_id)
            async with lock:
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
                    await log_action(self.db_connector, user_id, f"Added to waitlist for event {event_id}")
                    return {"status": "fail", "message": f"No tickets available. User {user_id} added to waitlist."}

                await self.db_connector.execute_query(
                    "INSERT INTO reservations (user_id, event_id) VALUES (?, ?)",
                    params=(user_id, event_id)
                )
                await self.db_connector.execute_query(
                    "UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?",
                    params=(event_id,)
                )
                await log_action(self.db_connector, user_id, f"Reserved ticket for event {event_id}")
                return {"status": "success", "message": f"Ticket reserved for User {user_id} for event {event_id}"}
        except Exception as e:
            logger.error(f"Error in reserve_ticket: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_waitlist(self, event_id):
        """대기자 목록 처리"""
        try:
            waitlist_user = await self.db_connector.execute_query(
                "SELECT user_id FROM waitlist WHERE event_id = ? ORDER BY id ASC LIMIT 1",
                params=(event_id,),
                fetch_one=True
            )
            if not waitlist_user:
                logger.info(f"No users in the waitlist for event {event_id}.")
                return

            waitlist_user_id = waitlist_user[0]
            logger.debug(f"Processing waitlist for user {waitlist_user_id} for event {event_id}")

            if waitlist_user_id in self.clients:
                reader, writer = self.clients[waitlist_user_id]
                message = f"Ticket available for Event {event_id}."
                try:
                    writer.write(message.encode())
                    await writer.drain()
                    logger.info(f"Notification sent to user {waitlist_user_id}.")
                except Exception as e:
                    logger.error(f"Error sending message to user {waitlist_user_id}: {e}")
                    del self.clients[waitlist_user_id]
                    writer.close()
                    await writer.wait_closed()

            await self.db_connector.execute_query(
                "DELETE FROM waitlist WHERE user_id = ? AND event_id = ?",
                params=(waitlist_user_id, event_id)
            )
            await log_action(self.db_connector, waitlist_user_id, f"Notified about available ticket for event {event_id}")
        except Exception as e:
            logger.error(f"Error in handle_waitlist: {e}")

    async def cancel_reservation(self, user_id, event_id):
        """예약 취소"""
        try:
            lock = await self.get_event_lock(event_id)
            async with lock:
                reservation_exists = await self.db_connector.execute_query(
                    "SELECT id FROM reservations WHERE user_id = ? AND event_id = ?",
                    params=(user_id, event_id),
                    fetch_one=True
                )
                if not reservation_exists:
                    return {"status": "fail", "message": f"No reservation found for User {user_id} on Event {event_id}"}

                await self.db_connector.execute_query(
                    "DELETE FROM reservations WHERE user_id = ? AND event_id = ?",
                    params=(user_id, event_id)
                )
                await self.db_connector.execute_query(
                    "UPDATE events SET available_tickets = available_tickets + 1 WHERE id = ?",
                    params=(event_id,)
                )
                await self.handle_waitlist(event_id)
                await log_action(self.db_connector, user_id, f"Canceled reservation for event {event_id}")
                return {"status": "success", "message": f"Reservation canceled for User {user_id} on Event {event_id}"}
        except Exception as e:
            logger.error(f"Error in cancel_reservation: {e}")
            return {"status": "error", "message": str(e)}

    async def get_all_events(self):
        """모든 이벤트 조회"""
        try:
            events = await self.db_connector.execute_query("SELECT * FROM events", fetch_all=True)
            if not events:
                return {"status": "success", "message": "No events available"}
            return {
                "status": "success",
                "events": [
                    {
                        "id": event[0],
                        "name": event[1],
                        "description": event[2],
                        "date": event[3],
                        "available_tickets": event[4],
                    }
                    for event in events
                ],
            }
        except Exception as e:
            logger.error(f"Error in get_all_events: {e}")
            return {"status": "error", "message": str(e)}

    async def get_user_logs(self, user_id):
        """사용자 로그 조회"""
        try:
            logs = await self.db_connector.execute_query(
                "SELECT action, timestamp FROM logs WHERE user_id = ? ORDER BY timestamp DESC",
                params=(user_id,),
                fetch_all=True
            )
            if not logs:
                return {"status": "success", "message": "No logs found"}
            return {
                "status": "success",
                "logs": [
                    {"action": log[0], "timestamp": log[1]}
                    for log in logs
                ],
            }
        except Exception as e:
            logger.error(f"Error in get_user_logs: {e}")
            return {"status": "error", "message": str(e)}

async def log_action(db_connector: AsyncDatabaseConnector, user_id, action):
    """사용자 활동 로그 기록"""
    try:
        await db_connector.execute_query(
            "INSERT INTO logs (user_id, action, timestamp) VALUES (?, ?, datetime('now'))",
            params=(user_id, action)
        )
    except Exception as e:
        logger.error(f"Error in log_action: {e}")
