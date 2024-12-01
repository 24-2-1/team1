class Notifications:
    def __init__(self, client_socket):
        self.client_socket = client_socket

    def check_notifications(self, user):
        response = self.client_socket.send_request(f"check_notifications {user}")
        print(f"{user}님의 알림: {response}")
