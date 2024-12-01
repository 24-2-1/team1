from auth import Auth
from socket_client import ClientSocket
from reservation import Reservation
from notifications import Notifications

class CLIApp:
    def __init__(self):
        self.auth = Auth()  # 인증 처리
        self.client_socket = ClientSocket()  # 서버와 통신을 위한 소켓 객체
        self.logged_in_user = None
        self.reservation = Reservation(self.client_socket)  # 예약 처리
        self.notifications = Notifications(self.client_socket)  # 알림 처리

    def show_initial_menu(self):
        print("\n===== 초기 메뉴 =====")
        print("1. 회원가입")
        print("2. 로그인")
        print("3. 예약 목록 보기")
        print("0. 종료")

    def show_logged_in_menu(self):
        print("\n===== 메뉴 =====")
        print("1. 티켓 예약")
        print("2. 대기자 등록")
        print("3. 알림 확인")
        print("0. 로그아웃")

    def handle_reservation(self):
        if self.logged_in_user:
            self.reservation.reserve_ticket(self.logged_in_user)

    def handle_waitlist(self):
        if self.logged_in_user:
            self.reservation.add_to_waitlist(self.logged_in_user)

    def handle_notifications(self):
        if self.logged_in_user:
            self.notifications.check_notifications(self.logged_in_user)

    def run(self):
        while True:
            if self.logged_in_user:
                self.show_logged_in_menu()
            else:
                self.show_initial_menu()

            choice = input("메뉴를 선택하세요: ").strip()
            if self.logged_in_user:
                if choice == "1":
                    self.handle_reservation()
                elif choice == "2":
                    self.handle_waitlist()
                elif choice == "3":
                    self.handle_notifications()
                elif choice == "0":
                    print(f"{self.logged_in_user}님, 로그아웃되었습니다.")
                    self.logged_in_user = None
                else:
                    print("올바르지 않은 선택입니다. 다시 시도하세요.")
            else:
                if choice == "1":
                    self.auth.register_user()
                elif choice == "2":
                    self.auth.login_user()
                elif choice == "3":
                    self.auth.view_reservations()
                elif choice == "0":
                    print("프로그램을 종료합니다.")
                    break
                else:
                    print("올바르지 않은 선택입니다. 다시 시도하세요.")

if __name__ == "__main__":
    app = CLIApp()
    app.run()
