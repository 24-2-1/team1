class Auth:
    def __init__(self):
        self.users = {}  # 사용자의 정보 (간단한 딕셔너리로 처리)

    def register_user(self):
        username = input("사용자 이름을 입력하세요: ")
        password = input("비밀번호를 입력하세요: ")
        if username in self.users:
            print("이미 존재하는 사용자입니다.")
        else:
            self.users[username] = password
            print(f"{username}님, 회원가입이 완료되었습니다.")

    def login_user(self):
        username = input("사용자 이름을 입력하세요: ")
        password = input("비밀번호를 입력하세요: ")
        if self.users.get(username) == password:
            print(f"{username}님, 로그인 되었습니다.")
            return username
        else:
            print("잘못된 사용자 이름 또는 비밀번호입니다.")
            return None

    def view_reservations(self):
        print("예약 목록을 조회합니다.")
        # 서버에서 예약 목록을 가져오는 코드 추가
