import asyncio
import json
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
            'register': lambda args: self.user_service.register_user(args.get("userid"), args.get("password")),
            'login': lambda args: self.user_service.login(args.get("userid"), args.get("password")),
            'view_events': lambda _: self.event_service.get_all_events(),
            'reserve_ticket': lambda args: self.event_service.reserve_ticket(args.get("userid"), args.get("event_id")),
            'cancel': lambda args: self.event_service.cancel_reservation(args.get("userid"), args.get("event_id")),
        }

    async def handle_command(self, request):
        """명령어 처리"""
        try:
            command_type = request.get("type")
            data = request.get("data", {})

            if command_type in self.command_map:
                return await self.command_map[command_type](data)
            else:
                return {"status": "error", "message": "Unknown command"}
        except Exception as e:
            print(f"Error in handle_command: {e}")
            return {"status": "error", "message": str(e)}

class SocketServer:
    """소켓 서버 클래스"""
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.clients = {}
        self.db_connector = AsyncDatabaseConnector()
        self.user_service = AsyncUserService(self.db_connector)
        self.event_service = AsyncEventService(self.db_connector, self.clients)
        self.command_handler = CommandHandler(self.user_service, self.event_service)

    async def handle_client(self, reader, writer):
        """클라이언트 요청 처리"""
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    print(f"Connection closed by client: {addr}")
                    break

                try:
                    request = json.loads(data.decode())
                    print(f"Received: {request}")

                    # 명령어 처리
                    response = await self.command_handler.handle_command(request)
                except json.JSONDecodeError:
                    response = {"status": "error", "message": "Invalid JSON format"}

                # 응답 전송
                writer.write(json.dumps(response).encode())
                await writer.drain()

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"Disconnected from {addr}")

    async def start(self):
        """서버 시작"""
        await initialize_database()
        print("Database initialized")

        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"Server started on {self.host}:{self.port}")

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    server = SocketServer()
    asyncio.run(server.start())
