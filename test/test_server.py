import asyncio
from Component.user_service import AsyncUserService
from testdb import AsyncDatabaseConnector, initialize_database

HOST = '127.0.0.1'
PORT = 65433

# 데이터베이스 연결 및 UserService 초기화
db_connector = AsyncDatabaseConnector("database.db")
user_service = AsyncUserService(db_connector)

clients = {}  # 현재 로그인된 사용자 (userid: writer)


async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    current_user = None  # 현재 로그인된 사용자의 ID를 추적
    print(f"클라이언트 연결: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode('utf-8').strip()

            if message.startswith("REGISTER"):
                _, userid, password = message.split(":", 2)
                response = await user_service.register_user(userid, password)
                writer.write(response.encode('utf-8'))

            elif message.startswith("LOGIN"):
                _, userid, password = message.split(":", 2)
                response = await user_service.login(userid, password)
                if response != "로그인 실패":
                    clients[userid] = writer
                    current_user = userid
                    writer.write("로그인 성공".encode('utf-8'))
                else:
                    writer.write(response.encode('utf-8'))

            elif message.startswith("MESSAGE"):
                if current_user is None:
                    writer.write("로그인이 필요합니다.".encode('utf-8'))
                    continue
                _, raw_message = message.split(":", 1)
                target, msg = raw_message.split(":", 1)
                if target in clients:
                    target_writer = clients[target]
                    target_writer.write(f"{current_user}님으로부터 메시지: {msg}".encode('utf-8'))
                else:
                    writer.write(f"사용자 {target}이 로그인 상태가 아닙니다.".encode('utf-8'))

            await writer.drain()
    except Exception as e:
        print(f"클라이언트 처리 중 오류: {e}")
    finally:
        if current_user in clients:
            del clients[current_user]
        writer.close()
        await writer.wait_closed()
        print(f"클라이언트 연결 종료: {addr}")


async def main():
    await initialize_database()
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f"서버가 {HOST}:{PORT}에서 시작되었습니다.")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())