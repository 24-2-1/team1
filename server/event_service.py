import threading

class EventService:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.locks = {}  # 이벤트별 락 관리
        self.locks_lock = threading.Lock()  # 락 관리에 대한 동기화

    def get_event_lock(self, event_id):
        """이벤트 ID별 락 반환, 없으면 생성"""
        with self.locks_lock:
            if event_id not in self.locks:
                self.locks[event_id] = threading.Lock()
            return self.locks[event_id]

    def reserve_ticket(self, user_id, event_id):
        """티켓 예약 (락 적용)"""
        event_lock = self.get_event_lock(event_id)  # 이벤트별 락 획득
        with event_lock:  # 특정 이벤트에 대해 락 적용
            try:
                available_tickets = self.db_connector.execute_query(
                    'SELECT available_tickets FROM events WHERE id = ?',
                    (event_id,),
                    fetch_one=True
                )
                if not available_tickets:
                    return f"Error: Event {event_id} does not exist"
                if available_tickets[0] <= 0:
                    return f"Error: No available tickets for event {event_id}"

                # 예약 처리
                self.db_connector.execute_query(
                    'INSERT INTO reservations (user_id, event_id) VALUES (?, ?)', (user_id, event_id)
                )
                self.db_connector.execute_query(
                    'UPDATE events SET available_tickets = available_tickets - 1 WHERE id = ?',
                    (event_id,)
                )
                return f"User {user_id} reserved a ticket for event {event_id}"
            except Exception as e:
                print(f"Unexpected error during reservation: {e}")
                return "Error: Reservation failed"

    def cancel_reservation(self, user_id, event_id):
        """예약 취소 (락 적용)"""
        event_lock = self.get_event_lock(event_id)  # 이벤트별 락 획득
        with event_lock:  # 특정 이벤트에 대해 락 적용
            try:
                self.db_connector.execute_query(
                    'DELETE FROM reservations WHERE user_id = ? AND event_id = ?', (user_id, event_id)
                )
                self.db_connector.execute_query(
                    'UPDATE events SET available_tickets = available_tickets + 1 WHERE id = ?', (event_id,)
                )
                return f"Reservation canceled for User {user_id} on Event {event_id}"
            except Exception as e:
                print(f"Unexpected error during cancellation: {e}")
                return "Error: Cancellation failed"

    
    def view_logs(self):
        """로그 조회"""
        try:
            logs = self.execute_query('SELECT * FROM logs', fetch_all=True)
            return "\n".join([str(log) for log in logs])
        except Exception as e:
            print(f"Unexpected error during log retrieval: {e}")
            return "Error: Log retrieval failed"
