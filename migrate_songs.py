import asyncio
import aiosqlite
from pathlib import Path

async def migrate():
    # Using relative path from src/config default
    db_path = Path('c:/Users/uzzo/Desktop/VEXO3/data/musicbot.db')
    print(f'Migrating database at: {db_path}')
    async with aiosqlite.connect(db_path) as db:
        try:
            await db.execute('ALTER TABLE songs ADD COLUMN is_ephemeral BOOLEAN DEFAULT 0')
            await db.commit()
            print('Migration successful: Added is_ephemeral column')
        except Exception as e:
            print(f'Migration skipped/failed: {e}')

if __name__ == '__main__':
    asyncio.run(migrate())
