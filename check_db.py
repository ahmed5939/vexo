import asyncio
import aiosqlite
from pathlib import Path

async def check():
    db_path = Path("data/musicbot.db")
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT COUNT(*) FROM song_library_entries") as cursor:
            row = await cursor.fetchone()
            print(f"Library entries: {row[0]}")
        async with db.execute("SELECT COUNT(*) FROM songs") as cursor:
            row = await cursor.fetchone()
            print(f"Total songs: {row[0]}")
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            print(f"Total users: {row[0]}")

if __name__ == "__main__":
    asyncio.run(check())
