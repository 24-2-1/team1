import asyncio
from DB.db import initialize_database, AsyncDatabaseConnector
from Component.user_service import AsyncUserService
from Component.event_service import AsyncEventService

class CommandHandler:
    """명령어 처리 클래스"""
    def __init__(self, user_service, event_service):
        self.user_service = user_service
        self.event_service = event_service

        # 명령어-처리 함수 매핑
        self.command_map = {
            'register': lambda args: self.user_service.register_user(*args),
            'login': lambda args: self.user_service.login(*args),
            'reserve': lambda args: self.event_service.reserve_ticket(*map(int, args)),
            'cancel': lambda args: self.event_service.cancel_reservation(*map(int, args)),
            'view_events': lambda args: self.event_service.get_all_events(),  # 수정
            'view_logs': lambda args: self.event_service.get_user_logs(int(args[0]))  # 추가된 명령어
        }

    async def handle_command(self, data):
        """명령어 처리"""
        try:
            commands = data.strip().split(' ')
            command = commands[0].lower()

            if command in self.command_map:
                return await self.command_map[command](commands[1:])
            else:
                return "Error: Unknown command"

        except TypeError:
            return "Error: Invalid arguments"
        except Exception as e:
            print(f"Unexpected error in handle_command: {e}")
            return "Error: Request failed"

class SocketServer:
    """소켓 서버 클래스"""
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.db_connector = AsyncDatabaseConnector()
        self.user_service = AsyncUserService(self.db_connector)
        self.event_service = AsyncEventService(self.db_connector)
        self.command_handler = CommandHandler(self.user_service, self.event_service)

    async def handle_client(self, reader, writer):
        """클라이언트 요청 처리"""
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")

        try:
            while True:
                try:
                    data = await reader.read(1024)
                    if not data:  # 클라이언트 연결 종료
                        print(f"Connection closed by client: {addr}")
                        break

                    message = data.decode().strip()
                    print(f"Received: {message} from {addr}")

                    # 명령어 처리
                    response = await self.command_handler.handle_command(message)
                    writer.write(response.encode())
                    await writer.drain()

                except Exception as e:
                    print(f"Error handling request from {addr}: {e}")
                    writer.write(f"Error: {e}".encode())
                    await writer.drain()

        except asyncio.CancelledError:
            # 클라이언트 연결 강제 종료 처리
            print(f"Client connection cancelled: {addr}")
        except Exception as e:
            print(f"Unexpected error with client {addr}: {e}")
        finally:
            # 연결 종료 시 자원 정리
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
