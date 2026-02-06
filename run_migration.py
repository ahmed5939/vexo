import asyncio
import aiosqlite
from pathlib import Path

async def migrate():
    db_path = Path("data/musicbot.db")
    schema_path = Path("src/database/migrations/lib_schema.sql")
    
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        return

    async with aiosqlite.connect(db_path) as db:
        schema = schema_path.read_text()
        await db.executescript(schema)
        await db.commit()
    print("Migration successful")

if __name__ == "__main__":
    asyncio.run(migrate())
