from socket_client import ClientSocket  # ClientSocket 클래스를 임포트하여 서버와의 통신 처리

class CLIApp:
    def __init__(self):
        self.logged_in_user = None  # 로그인된 사용자 정보 (없으면 None)
        self.client_socket = ClientSocket()  # 서버와 통신을 위한 클라이언트 소켓 객체

    def show_initial_menu(self):
        """초기 메뉴를 화면에 출력하는 함수"""
        print("\n===== 초기 메뉴 =====")
        print("1. 회원가입")  # 회원가입 선택지
        print("2. 로그인")  # 로그인 선택지
        print("3. 예약 목록 보기")  # 예약 목록 보기 선택지
        print("0. 종료")  # 프로그램 종료 선택지

    def show_logged_in_menu(self):
        """로그인 후 사용자 메뉴를 화면에 출력하는 함수"""
        print("\n===== 로그인 후 메뉴 =====")
        print("1. 티켓 예약")  # 티켓 예약 선택지
        print("2. 대기자 등록")  # 대기자 등록 선택지
        print("3. 알림 확인")  # 알림 확인 선택지
        print("0. 로그아웃")  # 로그아웃 선택지
        # 뒤로가기는 로그인 후 메뉴에서는 제외

    def handle_user_action(self, choice):
        """로그인한 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.handle_reservation,  # 티켓 예약 처리
            "2": self.handle_waitlist,  # 대기자 등록 처리
            "3": self.check_notifications,  # 알림 확인 처리
            "0": self.logout,  # 로그아웃 처리
        }
        return self._handle_action(actions, choice)  # 선택한 액션 처리

    def handle_guest_action(self, choice):
        """로그인하지 않은 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.register_user,  # 회원가입 처리
            "2": self.login_user,  # 로그인 처리
            "3": self.view_reservations,  # 예약 목록 보기 처리
            "0": self.exit_program,  # 프로그램 종료 처리
        }
        return self._handle_action(actions, choice)  # 선택한 액션 처리

    def _handle_action(self, actions, choice):
        """공통된 행동 처리 로직: 유효한 선택인지 확인 후 해당 처리 함수 호출"""
        action = actions.get(choice)  # 사용자가 선택한 옵션에 맞는 액션을 찾음
        if action:
            action()  # 선택한 액션을 실행
            return True
        else:
            print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리
            return False

    def go_back(self):
        """뒤로가기 버튼을 눌렀을 때 이전 메뉴로 돌아가는 함수"""
        print("이전 메뉴로 돌아갑니다.")

    def run(self):
        """프로그램 실행 함수: 사용자 선택에 따라 메뉴를 반복 출력하며 처리"""
        while True:
            if self.logged_in_user:
                # 로그인된 상태에서 메뉴 출력
                self.show_logged_in_menu()
                choice = input("메뉴를 선택하세요: ").strip()
                if not self.handle_user_action(choice):  # 잘못된 선택 시 다시 시도
                    continue
            else:
                # 로그인되지 않은 상태에서 메뉴 출력
                self.show_initial_menu()
                choice = input("메뉴를 선택하세요: ").strip()
                if not self.handle_guest_action(choice):  # 잘못된 선택 시 프로그램 종료
                    break

    def handle_reservation(self):
        """티켓 예약 처리 함수"""
        while True:
            print("\n===== 티켓 예약 =====")
            print("1. 예약하기")
            print("b. 뒤로가기")
            choice = input("메뉴를 선택하세요: ").strip()
            if choice == "1":
                print("예약을 처리합니다.")  # 실제 예약 처리 로직은 여기에 추가
            elif choice == "b":
                self.go_back()  # 뒤로가기 처리
                break
            else:
                print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리

    def handle_waitlist(self):
        """대기자 등록 처리 함수"""
        while True:
            print("\n===== 대기자 등록 =====")
            print("1. 대기자 등록")
            print("b. 뒤로가기")
            choice = input("메뉴를 선택하세요: ").strip()
            if choice == "1":
                print("대기자 등록을 처리합니다.")  # 실제 대기자 등록 로직은 여기에 추가
            elif choice == "b":
                self.go_back()  # 뒤로가기 처리
                break
            else:
                print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리

    def check_notifications(self):
        """알림 확인 처리 함수"""
        while True:
            print("\n===== 알림 확인 =====")
            print("1. 알림 확인")
            print("b. 뒤로가기")
            choice = input("메뉴를 선택하세요: ").strip()
            if choice == "1":
                print("알림을 확인합니다.")
                response = self.client_socket.send_request("view_notifications")  # 서버에서 알림 요청
                if response:
                    print("서버로부터 받은 알림:")  # 받은 알림 출력
                    print(response)
                else:
                    print("알림을 받을 수 없습니다.")  # 알림이 없거나 받지 못한 경우
            elif choice == "b":
                self.go_back()  # 뒤로가기 처리
                break
            else:
                print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리

    def register_user(self):
        """회원가입 처리 함수"""
        while True:
            print("\n===== 회원가입 =====")
            username = input("아이디를 입력하세요: ")
            password = input("비밀번호를 입력하세요: ")
            confirm_password = input("비밀번호 확인: ")
            
            if password == confirm_password:
                print(f"{username}님, 회원가입이 완료되었습니다.")  # 회원가입 완료 처리
                break
            else:
                print("비밀번호가 일치하지 않습니다. 다시 시도해주세요.")
                choice = input("뒤로 가시려면 'b'를 누르세요: ")
                if choice == "b":
                    self.go_back()
                    break

    def login_user(self):
        """로그인 처리 함수"""
        while True:
            print("\n===== 로그인 =====")
            username = input("아이디를 입력하세요: ")
            if username == "b":  # 뒤로 가기를 위한 처리
                self.go_back()
                break
            password = input("비밀번호를 입력하세요: ")
            
            # 로그인 로직 (간단히 구현)
            if username and password:
                self.logged_in_user = username
                print(f"{username}님, 로그인 되었습니다.")
                break
            else:
                print("아이디 또는 비밀번호를 입력해 주세요.")
            
            choice = input("뒤로 가시려면 'b'를 누르세요: ")
            if choice == "b":
                self.go_back()
                break

    def view_reservations(self):
        """예약 목록 보기 함수"""
        while True:
            print("\n===== 예약 목록 보기 =====")
            print("1. 예약 목록 보기")
            print("b. 뒤로가기")
            choice = input("메뉴를 선택하세요: ").strip()
            if choice == "1":
                print("예약 목록을 확인합니다.")  # 실제 예약 목록 확인 로직은 여기에 추가
            elif choice == "b":
                self.go_back()  # 뒤로가기 처리
                break
            else:
                print("올바르지 않은 선택입니다. 다시 시도하세요.")  # 잘못된 선택 처리

    def logout(self):
        """로그아웃 처리 함수"""
        print(f"{self.logged_in_user}님, 로그아웃되었습니다.")  # 로그아웃 메시지 출력
        self.logged_in_user = None  # 로그인 정보 초기화

    def exit_program(self):
        """프로그램 종료 처리 함수"""
        print("프로그램을 종료합니다.")  # 종료 메시지 출력
        return False  # False를 반환하여 프로그램 종료


# 메인 실행 부분
if __name__ == "__main__":
    app = CLIApp()  # CLIApp 인스턴스를 생성하여 실행
    app.run()  # run() 메서드 호출로 프로그램 실행
