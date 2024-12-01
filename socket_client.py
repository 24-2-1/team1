class ClientSocket:
    def __init__(self):
        # 서버 연결 관련 부분을 제거
        # self.host = "localhost"
        # self.port = 12345
        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.client_socket.connect((self.host, self.port))

        # 서버와의 연결 없이 기본적인 속성만 초기화
        self.data = []

    # 서버 연결 없이 데이터를 다루는 메소드로 수정
    def send_request(self, request):
        # 예시로 로컬 데이터 처리
        if request == "view_logs":
            return "최근 로그: 사용자 로그인 기록, 예약 시도 기록 등"
        return "요청을 처리할 수 없습니다."

    def receive_response(self):
        return self.data  # 받은 데이터가 없으므로 빈 데이터 반환
