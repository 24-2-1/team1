class Reservation:
    def __init__(self, client_socket):
        self.client_socket = client_socket

    def reserve_ticket(self, user):
        response = self.client_socket.send_request(f"reserve {user}")
        print(response)

    def add_to_waitlist(self, user):
        response = self.client_socket.send_request(f"waitlist {user}")
        print(response)
