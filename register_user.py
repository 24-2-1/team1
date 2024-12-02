import asyncio
from DB.db import AsyncDatabaseConnector
from Component.user_service import AsyncUserService

async def test_register_user():
    db_connector = AsyncDatabaseConnector()
    user_service = AsyncUserService(db_connector)

    username = "testuser"
    password = "testpassword"
    result = await user_service.register_user(username, password)
    print(result)

asyncio.run(test_register_user())
