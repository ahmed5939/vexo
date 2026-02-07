"""
Smart Discord Music Bot - Main Entry Point
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

import discord
from discord.ext import commands

from src.utils.logging import get_logger, Category, Event

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
log = get_logger("bot")


class MusicBot(commands.Bot):
    """Smart Discord Music Bot with preference learning."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",  # Fallback prefix, we use slash commands
            intents=intents,
            help_command=None,
        )
        
        # Will be initialized in setup_hook
        self.db = None
        self.discovery = None
        self.preferences = None
    
    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        log.event(Category.SYSTEM, "setup_started")
        
        # Store start time for uptime tracking
        from datetime import datetime, UTC
        self._start_time = datetime.now(UTC)
        
        # Initialize database
        from src.config import config
        from src.database.connection import DatabaseManager
        from src.database.crud import SongCRUD, UserCRUD, GuildCRUD, PlaybackCRUD, PreferenceCRUD, ReactionCRUD
        
        self.db = await DatabaseManager.create(config.DATABASE_PATH)
        log.event(Category.DATABASE, "initialized", path=config.DATABASE_PATH)
        
        # Initialize services
        from src.services.youtube import YouTubeService
        from src.services.spotify import SpotifyService
        from src.services.normalizer import SongNormalizer
        from src.services.discovery import DiscoveryEngine
        from src.services.preferences import PreferenceManager
        
        self.youtube = YouTubeService(config.YTDL_COOKIES_PATH, config.YTDL_PO_TOKEN)
        self.spotify = SpotifyService(config.SPOTIFY_CLIENT_ID, config.SPOTIFY_CLIENT_SECRET)
        self.normalizer = SongNormalizer(self.youtube)
        
        
        # Initialize CRUD helpers
        pref_crud = PreferenceCRUD(self.db)
        playback_crud = PlaybackCRUD(self.db)
        reaction_crud = ReactionCRUD(self.db)
        song_crud = SongCRUD(self.db)
        user_crud = UserCRUD(self.db)
        
        # Initialize discovery engine
        self.discovery = DiscoveryEngine(
            youtube=self.youtube,
            spotify=self.spotify,
            normalizer=self.normalizer,
            preference_crud=pref_crud,
            playback_crud=playback_crud,
            reaction_crud=reaction_crud,
        )
        
        # Initialize preference manager
        self.preferences = PreferenceManager(pref_crud, song_crud, user_crud)
        
        log.event(Category.SYSTEM, "services_initialized")
        
        # Load all cogs from the cogs directory
        cogs_dir = Path(__file__).parent / "cogs"
        if cogs_dir.exists():
            for cog_file in cogs_dir.glob("*.py"):
                if cog_file.name.startswith("_"):
                    continue
                cog_name = f"src.cogs.{cog_file.stem}"
                try:
                    await self.load_extension(cog_name)
                    log.event(Category.SYSTEM, Event.COG_LOADED, cog=cog_name)
                except Exception as e:
                    log.event(Category.SYSTEM, "cog_load_failed", level=logging.ERROR, cog=cog_name, error=str(e))
        
        # Sync slash commands
        log.event(Category.SYSTEM, "commands_syncing")
        await self.tree.sync()
        log.event(Category.SYSTEM, "commands_synced")
    
    async def on_ready(self) -> None:
        """Called when the bot is fully ready."""
        log.event(Category.SYSTEM, Event.BOT_READY, user=str(self.user), user_id=self.user.id, guilds=len(self.guilds))
        
        # Set presence
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/play"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when the bot joins a new guild."""
        log.event(Category.SYSTEM, Event.GUILD_JOINED, guild=guild.name, guild_id=guild.id)
        
        # Check max servers limit
        if self.db:
            from src.database.crud import SystemCRUD
            crud = SystemCRUD(self.db)
            limit = await crud.get_global_setting("max_concurrent_servers")
            
            if limit is not None:
                try:
                    limit_int = int(limit)
                    if len(self.guilds) > limit_int:
                        log.event(Category.SYSTEM, "server_limit_exceeded", level=logging.WARNING, limit=limit_int, guild=guild.name)
                        await guild.leave()
                        await crud.add_notification(
                            "warning", 
                            f"Auto-left server '{guild.name}' because the limit of {limit_int} servers was exceeded."
                        )
                except ValueError:
                    pass
    
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Called when the bot is removed from a guild."""
        log.event(Category.SYSTEM, Event.GUILD_LEFT, guild=guild.name, guild_id=guild.id)
    
    async def close(self) -> None:
        """Cleanup when the bot is shutting down."""
        log.event(Category.SYSTEM, "shutdown_started")
        
        # Disconnect from all voice channels
        for vc in self.voice_clients:
            try:
                await vc.disconnect(force=True)
            except Exception:
                pass
        
        await super().close()


async def main():
    """Main entry point."""
    from src.config import config
    
    bot = MusicBot()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        log.event(Category.SYSTEM, "shutdown_signal")
        asyncio.create_task(bot.close())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    try:
        await bot.start(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        log.event(Category.SYSTEM, "keyboard_interrupt")
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
