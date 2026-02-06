import asyncio
import aiosqlite
from pathlib import Path

async def seed_library():
    db_path = Path("data/musicbot.db")
    async with aiosqlite.connect(db_path) as db:
        # 1. From playback history (user requests)
        print("Seeding from playback history...")
        await db.execute("""
            INSERT OR IGNORE INTO song_library_entries (user_id, song_id, source, added_at)
            SELECT DISTINCT for_user_id, song_id, 'request', played_at
            FROM playback_history
            WHERE for_user_id IS NOT NULL AND discovery_source = 'user_request'
        """)
        
        # 2. From likes
        print("Seeding from reactions...")
        await db.execute("""
            INSERT OR IGNORE INTO song_library_entries (user_id, song_id, source, added_at)
            SELECT user_id, song_id, 'like', created_at
            FROM song_reactions
            WHERE reaction = 'like'
        """)
        
        # 3. From imported playlists
        print("Seeding from imports...")
        # (This is harder because we don't have the song associations for old imports 
        # stored in song_library_entries, but we can't easily retroactively link them
        # unless we re-process. Let's skip for now or just do what we can)
        
        await db.commit()
    print("Seeding complete")

if __name__ == "__main__":
    asyncio.run(seed_library())
