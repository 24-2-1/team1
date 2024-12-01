import asyncio
from DB.db import AsyncDatabaseConnector
from Component.event_service import AsyncEventService

async def test_get_all_events():
    db_connector = AsyncDatabaseConnector()
    event_service = AsyncEventService(db_connector)

    events = await event_service.get_all_events()
    print(events)

asyncio.run(test_get_all_events())
