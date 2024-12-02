from collections import deque #예약 시스템에서 대기자 목록 큐 형식으로 처리하려면 필요/ 항목 빠르게 제거하거나 새 항목 추가하는데 효율적
from datetime import datetime #로그 기록을 포함하여,날짜와 시간을 정확히 기록하고 처리

# 예약 관리 클래스
class ReservationManager:
    def __init__(self):
        self.reservations = []  # 예약 목록 (최대 5명)
        self.waitlist = deque()  # 대기자 목록 (FIFO 큐 방식)
        self.capacity = 5  # 최대 예약 가능 인원 수
        self.log_file = "event_ticket_logs.txt"  # 로그 기록을 위한 파일 경로

    def log_action(self, action, details=""):
        """로그 기록 함수: 작업과 관련된 정보를 로그 파일에 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 시간
        log_entry = f"[{timestamp}] {action}: {details}\n"  # 로그 항목 생성
        with open(self.log_file, "a") as log:  # 로그 파일에 기록
            log.write(log_entry)

    def add_reservation(self, name):
        """예약 추가: 예약이 가능한 경우 목록에 추가하고, 가득 찼으면 대기자로 등록"""
        if len(self.reservations) < self.capacity:
            self.reservations.append(name)  # 예약 목록에 추가
            print(f"\n{name}님의 예약이 완료되었습니다.")
            self.log_action("예약 성공", f"사용자: {name}")  # 로그 기록
        else:
            self.waitlist.append(name)  # 대기자 목록에 추가
            print(f"\n{name}님이 대기자로 등록되었습니다.")
            self.log_action("대기자 등록", f"사용자: {name}")  # 로그 기록

    def cancel_reservation(self, name):
        """예약 취소: 예약된 사용자의 예약을 취소하고, 대기자가 있으면 예약으로 이동"""
        if name in self.reservations:
            self.reservations.remove(name)  # 예약 목록에서 삭제
            print(f"\n{name}님의 예약이 취소되었습니다.")
            self.log_action("\n예약 취소", f"사용자: {name}")  # 로그 기록
            if self.waitlist:  # 대기자가 있으면 대기자 목록에서 첫 번째 사람을 예약 목록에 추가
                next_in_line = self.waitlist.popleft()  # 대기자 목록에서 첫 번째 사람
                self.reservations.append(next_in_line)  # 예약 목록에 추가
                print(f"\n대기자 {next_in_line}님이 예약되었습니다.")
                self.log_action("\n대기자 이동", f"사용자: {next_in_line}")  # 로그 기록
        else:
            print(f"\n{name}님은 예약 목록에 없습니다.")
            self.log_action("\n예약 취소 실패", f"사용자: {name}")  # 로그 기록

    def show_reservations(self):
        """현재 예약 목록 출력: 예약된 사용자 목록을 출력"""
        if self.reservations:
            print("\n현재 예약된 사용자:", ", ".join(self.reservations))  # 예약된 사용자를 출력
        else:
            print("\n현재 예약된 사용자가 없습니다.")  # 예약된 사람이 없을 경우
        self.log_action("예약 목록 조회")  # 로그 기록

    def show_waitlist(self):
        """대기자 목록 출력: 대기 중인 사용자 목록을 출력"""
        if self.waitlist:
            print("\n현재 대기자 목록:", ", ".join(self.waitlist))  # 대기자 목록을 출력
        else:
            print("\n현재 대기자가 없습니다.")  # 대기자가 없을 경우
        self.log_action("대기자 목록 조회")  # 로그 기록


# CLI 인터페이스
def main():
    manager = ReservationManager()  # 예약 관리자 객체 생성

    while True:
        print("\n==== 이벤트 티켓 예약 시스템 ====")
        print("1: 예약 하기")
        print("2: 예약 취소")
        print("3: 예약 목록 조회")
        print("4: 대기자 목록 조회")
        print("5: 프로그램 종료")
        choice = input("\n메뉴를 선택하세요: ")

        if choice == "1":
            name = input("\n예약할 사용자 이름을 입력하세요: ")  # 예약할 사용자의 이름 입력
            manager.add_reservation(name)  # 예약 추가
        elif choice == "2":
            name = input("\n취소할 사용자 이름을 입력하세요: ")  # 취소할 사용자의 이름 입력
            manager.cancel_reservation(name)  # 예약 취소
        elif choice == "3":
            manager.show_reservations()  # 예약 목록 조회
        elif choice == "4":
            manager.show_waitlist()  # 대기자 목록 조회
        elif choice == "5":
            print("\n프로그램을 종료합니다.")  # 프로그램 종료 메시지
            break  # 프로그램 종료
        else:
            print("\n올바르지 않은 선택입니다. 다시 입력해주세요.")  # 잘못된 선택 시 메시지


if __name__ == "__main__":
    main()  # 프로그램 실행

######