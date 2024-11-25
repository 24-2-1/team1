class EventService:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def reserve_ticket(self, user_id, event_id):
        """티켓 예약"""
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
        """예약 취소"""
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
