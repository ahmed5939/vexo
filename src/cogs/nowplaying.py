"""
Now Playing UI - Enhanced embed with progress and controls
"""
import asyncio
import logging
from datetime import datetime, UTC
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from src.cogs.music import MusicCog, QueueItem

logger = logging.getLogger(__name__)


class NowPlayingView(discord.ui.View):
    """Interactive Now Playing controls."""
    
    def __init__(self, cog: "NowPlayingCog", guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
    
    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="np_pause")
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle pause/resume."""
        music = self.cog.music_cog
        if not music:
            return
        
        player = music.get_player(self.guild_id)
        if player.voice_client:
            if player.voice_client.is_playing():
                player.voice_client.pause()
                button.emoji = "▶️"
            elif player.voice_client.is_paused():
                player.voice_client.resume()
                button.emoji = "⏸️"
            await interaction.response.edit_message(view=self)
    
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="np_skip")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Vote to skip."""
        music = self.cog.music_cog
        if not music:
            return
        
        player = music.get_player(self.guild_id)
        if player.voice_client and player.is_playing:
            player.skip_votes.add(interaction.user.id)
            voice_members = [m for m in player.voice_client.channel.members if not m.bot]
            votes_needed = max(1, len(voice_members) // 2)
            
            if len(player.skip_votes) >= votes_needed:
                player.voice_client.stop()
                await interaction.response.send_message("⏭️ Skipped!", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"⏭️ Vote added ({len(player.skip_votes)}/{votes_needed})",
                    ephemeral=True
                )
    
    @discord.ui.button(emoji="❤️", style=discord.ButtonStyle.secondary, custom_id="np_like")
    async def like(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Like current song."""
        # Defer to preferences cog
        pref_cog = self.cog.bot.get_cog("PreferencesCog")
        if pref_cog:
            # Simulate the like command
            music = self.cog.music_cog
            if music:
                player = music.get_player(self.guild_id)
                if player.current:
                    await interaction.response.send_message(
                        f"❤️ Liked **{player.current.title}**!",
                        ephemeral=True
                    )
                    return
        await interaction.response.send_message("❌ Unable to like", ephemeral=True)
    
    @discord.ui.button(emoji="👎", style=discord.ButtonStyle.secondary, custom_id="np_dislike")
    async def dislike(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Dislike current song."""
        music = self.cog.music_cog
        if music:
            player = music.get_player(self.guild_id)
            if player.current:
                await interaction.response.send_message(
                    f"👎 Disliked **{player.current.title}**",
                    ephemeral=True
                )
                return
        await interaction.response.send_message("❌ Unable to dislike", ephemeral=True)


class NowPlayingCog(commands.Cog):
    """Enhanced Now Playing embed with live updates."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.np_messages: dict[int, discord.Message] = {}  # guild_id -> message
        self.np_channels: dict[int, int] = {}  # guild_id -> channel_id
    
    @property
    def music_cog(self):
        return self.bot.get_cog("MusicCog")
    
    async def cog_load(self):
        self.update_loop.start()
        logger.info("Now Playing cog loaded")
    
    async def cog_unload(self):
        self.update_loop.cancel()
    
    def create_embed(self, current: "QueueItem", queue_size: int = 0, is_paused: bool = False) -> discord.Embed:
        """Create the Now Playing embed."""
        status = "⏸️ Paused" if is_paused else "🎵 Now Playing"
        
        embed = discord.Embed(
            title=status,
            color=discord.Color.from_rgb(124, 58, 237)  # Purple
        )
        
        # Song info
        embed.add_field(
            name="🎶 Track",
            value=f"**{current.title}**",
            inline=True
        )
        embed.add_field(
            name="🎤 Artist",
            value=current.artist,
            inline=True
        )
        
        # Discovery info
        if current.discovery_reason:
            embed.add_field(
                name="✨ Discovery",
                value=current.discovery_reason,
                inline=False
            )
        
        # For user (democratic turn)
        if current.for_user_id:
            embed.add_field(
                name="🎯 Playing for",
                value=f"<@{current.for_user_id}>",
                inline=True
            )
        elif current.requester_id:
            embed.add_field(
                name="📨 Requested by",
                value=f"<@{current.requester_id}>",
                inline=True
            )
        
        # Queue info
        embed.add_field(
            name="📜 Queue",
            value=f"{queue_size} songs" if queue_size > 0 else "Empty",
            inline=True
        )
        
        # YouTube link
        yt_url = f"https://youtube.com/watch?v={current.video_id}"
        embed.add_field(
            name="🔗 Link",
            value=f"[YouTube]({yt_url})",
            inline=True
        )
        
        # Thumbnail (YouTube thumbnail)
        embed.set_thumbnail(url=f"https://img.youtube.com/vi/{current.video_id}/hqdefault.jpg")
        
        embed.set_footer(text="Use buttons below to control playback")
        embed.timestamp = datetime.now(UTC)
        
        return embed
    
    async def send_now_playing(self, guild_id: int, channel: discord.TextChannel):
        """Send or update the Now Playing message."""
        music = self.music_cog
        if not music:
            return
        
        player = music.get_player(guild_id)
        if not player.current:
            return
        
        is_paused = player.voice_client.is_paused() if player.voice_client else False
        embed = self.create_embed(player.current, player.queue.qsize(), is_paused)
        view = NowPlayingView(self, guild_id)
        
        # Delete old message if exists
        if guild_id in self.np_messages:
            try:
                await self.np_messages[guild_id].delete()
            except:
                pass
        
        # Send new message
        msg = await channel.send(embed=embed, view=view)
        self.np_messages[guild_id] = msg
        self.np_channels[guild_id] = channel.id
    
    @tasks.loop(seconds=15)
    async def update_loop(self):
        """Periodically update Now Playing embeds."""
        music = self.music_cog
        if not music:
            return
        
        for guild_id, msg in list(self.np_messages.items()):
            try:
                player = music.get_player(guild_id)
                if not player.current:
                    # Song ended, delete message
                    await msg.delete()
                    del self.np_messages[guild_id]
                    continue
                
                is_paused = player.voice_client.is_paused() if player.voice_client else False
                embed = self.create_embed(player.current, player.queue.qsize(), is_paused)
                await msg.edit(embed=embed)
            except Exception as e:
                logger.debug(f"Error updating NP for guild {guild_id}: {e}")
    
    @update_loop.before_loop
    async def before_update_loop(self):
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_track_start(self, guild_id: int, channel_id: int):
        """Called when a new track starts playing."""
        channel = self.bot.get_channel(channel_id)
        if channel:
            await self.send_now_playing(guild_id, channel)


async def setup(bot: commands.Bot):
    await bot.add_cog(NowPlayingCog(bot))
