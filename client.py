from Component.event_client import EventClient
     
class ViewClient(EventClient):
      
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
        print("0. 종료")  # 로그아웃 선택지
        # 뒤로가기는 로그인 후 메뉴에서는 제외

    def handle_guest_action(self, choice):
        """로그인하지 않은 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.register,  # 회원가입 처리
            "2": self.login,  # 로그인 처리
            "3": self.book_event, #뮤지컬 목록
            "9": self.exit_program,  # 프로그램 종료 처리
        }
        return self._handle_action(actions, choice)  # 선택한 액션 처리
    
    def handle_user_action(self, choice):
        """로그인한 사용자의 선택에 따른 행동 처리 함수"""
        actions = {
            "1": self.book_event,  # 티켓 예약 처리
            "2": self.handle_waitlist,  
            "3": self.check_notifications,  # 알림 확인 처리
            "0": self.logout,  # 로그아웃 처리
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
        
    """수정필요"""
    def run(self): 
        self.connect()
        """프로그램 실행 함수: 사용자 선택에 따라 메뉴를 반복 출력하며 처리"""
        while True:
            if self.login_user:
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
        self.close()

if __name__ == "__main__":
    client = ViewClient()
    client.run()
