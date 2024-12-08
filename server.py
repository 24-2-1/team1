import asyncio
from DB.db import initialize_database, AsyncDatabaseConnector
from Component.user_service import AsyncUserService
from Component.event_service import AsyncEventService
import logging

# 로그 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
class SpecificFunctionFilter(logging.Filter):
    """특정 함수의 로그만 필터링"""
    def __init__(self, functions):
        super().__init__()
        self.functions = functions

    def filter(self, record):
        # 로그 메시지에 특정 함수 이름이 포함되어 있는지 확인
        return any(func in record.msg for func in self.functions)
# 필터 추가
function_filter = SpecificFunctionFilter(functions=["[handle_waitlist]", "[cancel_reservation]"])
for handler in logging.getLogger().handlers:
    handler.addFilter(function_filter)


clients = {}
class CommandHandler:
    """명령어 처리 클래스"""
    def __init__(self, user_service, event_service):
        self.user_service = user_service
        self.event_service = event_service

        # 명령어-처리 함수 매핑
        self.command_map = {
            'register': lambda args: self.user_service.register_user(*args),
            'login': lambda args: self.user_service.login(*args),
            'logout': lambda args: self.user_service.logout(*args),
            'view_events': lambda args: self.event_service.get_all_events(*args),  # 수정
            'check_log': lambda args: self.event_service.get_user_logs(*args), # 알람확인
            'reserve_ticket': lambda args: self.event_service.reserve_ticket(*args),
            'cancel': lambda args: self.event_service.cancel_reservation(*args),
            'view_seat': lambda args: self.event_service.get_seat_availability(args[0]),  # 좌석 조회 추가
            'check_reservation_status': lambda args: self.event_service.get_all_reservations_for_user(*args)  # 예약 상태 조회 수정
        }

    async def handle_command(self, data,writer):
        """명령어 처리"""
        try:
            commands = data.strip().split(' ')
            command = commands[0].lower()

            if command in self.command_map:
                if command == 'view_events':
                    # view_events는 인자가 필요 없으므로 빈 리스트를 넘깁니다.
                    return await self.command_map[command]([])             
                # 모든 다른 명령어를 처리
                response = await self.command_map[command](commands[1:])
                if command == "login":
                    if response != "로그인 실패":
                        clients[commands[1]] = writer  # 로그인 성공 시 clients에 추가
                    return response
                return response              
            else:
                return f"client와 event_service 실행 함수가 달라"

        except TypeError:
            return "TypeError"
        except Exception as e:
            print(f"Unexpected error in handle_command: {e}")
            return f"그냥 에러"

class SocketServer:
    """소켓 서버 클래스"""
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.db_connector = AsyncDatabaseConnector()
        self.user_service = AsyncUserService(self.db_connector,clients)
        self.event_service = AsyncEventService(self.db_connector,clients)
        self.command_handler = CommandHandler(self.user_service, self.event_service)

    async def handle_client(self, reader, writer):
        """클라이언트 요청 처리"""
        addr = writer.get_extra_info('peername')
        current_user = None
        print(f"Connected to {addr}")

        try:
            while True:
                try:
                    data = await reader.read(1024)
                    if not data:  # 클라이언트 연결 종료
                        print(f"Connection closed by client: {addr}")
                        break

                    message = data.decode('utf-8').strip()
                    print(f"Received: {message} from {addr}")

                    # 명령어 처리
                    response = await self.command_handler.handle_command(message,writer)
                    writer.write(response.encode('utf-8'))
                    await writer.drain()
                    
                    if message.startswith("login"):
                        current_user = message.split(' ')[1]

                except Exception as e:
                    print(f"Error handling request from {addr}: {e}")
                    writer.write(f"Error: {e}".encode('utf-8'))
                    await writer.drain()

        except asyncio.CancelledError:
            # 클라이언트 연결 강제 종료 처리
            print(f"Client connection cancelled: {addr}")
        except Exception as e:
            print(f"Unexpected error with client {addr}: {e}")
        finally:
            # 연결 종료 시 자원 정리
            if current_user and current_user in clients:
                del clients[current_user]
            print(f"Disconnected from {addr}")
            writer.close()
            await writer.wait_closed()


    async def start(self):
        """서버 시작"""
        try:
            await initialize_database()  # 데이터베이스 초기화
            print("Database initialized")

            # 서버 시작
            server = await asyncio.start_server(self.handle_client, self.host, self.port)
            print(f"Server started on {self.host}:{self.port}")

            async with server:
                await server.serve_forever()
        except asyncio.CancelledError:
            # asyncio.CancelledError 처리
            print("\nServer shutting down gracefully (CancelledError).")
        except KeyboardInterrupt:
            # Ctrl+C로 서버 종료 시 처리
            print("\nServer interrupted by user (KeyboardInterrupt). Shutting down...")
        except Exception as e:
            # 서버 초기화 및 실행 중 발생한 예외 처리
            print(f"Error starting server: {e}")
        finally:
            print("Server shutting down. Goodbye!")

if __name__ == "__main__":
    server = SocketServer()
    asyncio.run(server.start())