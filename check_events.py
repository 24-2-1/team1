import aiosqlite

async def check_events():
    async with aiosqlite.connect("DB/event_system.db") as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM events")
            events = await cursor.fetchall()
            print("Events in database:")
            for event in events:
                print(event)

import asyncio
asyncio.run(check_events())
