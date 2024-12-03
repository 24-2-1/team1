from Component.event_client import EventClient
     
class ViewClient(EventClient):
    """Component디렉토리 안의 event_client.py를 부모로 상속, 서버로 보낼 모든 기능들은 거기서"""
    def __init__(self):
        super().__init__()
        
    def show_initial_menu(self):
        """초기 메뉴를 화면에 출력하는 함수"""
        print("\n===== 초기 메뉴 =====")
        print("1. 회원가입")  # 회원가입 선택지
        print("2. 로그인")  # 로그인 선택지
        print("3. 뮤지컬 목록 보기") 
        print("0. 종료")  # 프로그램 종료 선택지

    def show_logged_in_menu(self):
        """로그인 후 사용자 메뉴를 화면에 출력하는 함수"""
        print("\n===== 로그인 후 메뉴 =====")
        print("1. 뮤지컬 목록 보기")  # 대기자 등록 선택지
        print("2. 티켓 예약")  # 티켓 예약 선택지
        print("3. 알림 확인")  # 알림 확인 선택지
        print("9. 로그아웃")  # 로그아웃 선택지
        print("0. 종료")  

    def handle_guest_action(self, choice):
        """로그인하지 않은 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.register,  # 회원가입 처리
            "2": self.login,  # 로그인 처리
            "3": self.view_events, #뮤지컬 목록
        }
        return self._handle_action(actions, choice)  # 선택한 액션 처리
    
    def handle_user_action(self, choice):
        """로그인한 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.view_events,  # 티켓 예약 처리
            "3": self.check_notifications,  # 알림 확인 처리
            "9": self.logout,  # 로그아웃 처리
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
    
    def logout(self):
        self.login_user = None
    
    def run_menu(self):
        """프로그램 실행 함수: 사용자 선택에 따라 메뉴를 반복 출력하며 처리"""
        while True:
            if self.login_user:
                # 로그인된 상태에서 메뉴 출력
                self.show_logged_in_menu()
                choice = input("메뉴를 선택하세요: ").strip()
                if choice == "0":
                    print("프로그램을 종료합니다.")
                    self.close()  # 연결 종료
                    exit()  # 프로그램 완전히 종료
                if not self.handle_user_action(choice):  # 잘못된 선택 시 다시 시도
                    continue
            else:
                # 로그인되지 않은 상태에서 메뉴 출력
                self.show_initial_menu()
                choice = input("메뉴를 선택하세요: ").strip()
                if choice == "0":
                    print("프로그램을 종료합니다.")
                    self.close()  # 연결 종료
                    exit()  # 프로그램 완전히 종료
                if not self.handle_guest_action(choice):  # 잘못된 선택 시 프로그램 종료
                    continue


                

if __name__ == "__main__":
    client = ViewClient()
    client.connect()
    client.run_menu()
