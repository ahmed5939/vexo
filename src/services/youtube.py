"""
YouTube Music API Wrapper
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from functools import partial
from typing import Any

import yt_dlp
from ytmusicapi import YTMusic

logger = logging.getLogger(__name__)


@dataclass
class YTTrack:
    """YouTube track info."""
    video_id: str
    title: str
    artist: str
    duration_seconds: int | None = None
    album: str | None = None
    year: int | None = None
    thumbnail_url: str | None = None


class YouTubeService:
    """YouTube Music API wrapper."""
    
    def __init__(self, cookies_path: str | None = None, po_token: str | None = None):
        self.yt = YTMusic()
        self.cookies_path = cookies_path
        self.po_token = po_token
        self._ydl_opts = {
            "format": "bestaudio/best",
            "source_address": "0.0.0.0",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        if cookies_path:
            self._ydl_opts["cookiefile"] = cookies_path
        if po_token:
            self._ydl_opts["extractor_args"] = {"youtube": {"po_token": [po_token]}}
    
    async def search(self, query: str, filter_type: str = "songs", limit: int = 5) -> list[YTTrack]:
        """Search YouTube Music for tracks."""
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None,
                partial(self.yt.search, query, filter=filter_type, limit=limit)
            )
            
            tracks = []
            for r in results:
                if not r.get("videoId"):
                    continue
                
                duration = None
                if r.get("duration_seconds"):
                    duration = r["duration_seconds"]
                elif r.get("duration"):
                    # Parse duration string like "3:45"
                    duration = self._parse_duration(r["duration"])
                
                artist = "Unknown"
                if r.get("artists") and len(r["artists"]) > 0:
                    artist = r["artists"][0].get("name", "Unknown")
                
                tracks.append(YTTrack(
                    video_id=r["videoId"],
                    title=r.get("title", "Unknown"),
                    artist=artist,
                    duration_seconds=duration,
                    album=r.get("album", {}).get("name") if r.get("album") else None,
                    year=r.get("year"),
                    thumbnail_url=r.get("thumbnails", [{}])[-1].get("url"),
                ))
            
            return tracks
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return []
    
    async def get_watch_playlist(self, video_id: str, limit: int = 20) -> list[YTTrack]:
        """Get related tracks from a video's watch playlist."""
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None,
                partial(self.yt.get_watch_playlist, videoId=video_id, limit=limit)
            )
            
            tracks = []
            for t in results.get("tracks", []):
                if not t.get("videoId"):
                    continue
                
                artist = "Unknown"
                if t.get("artists") and len(t["artists"]) > 0:
                    artist = t["artists"][0].get("name", "Unknown")
                
                tracks.append(YTTrack(
                    video_id=t["videoId"],
                    title=t.get("title", "Unknown"),
                    artist=artist,
                    duration_seconds=t.get("length_seconds") or t.get("duration_seconds"),
                    year=t.get("year"),
                ))
            
            return tracks
        except Exception as e:
            logger.error(f"Error getting watch playlist: {e}")
            return []
    
    async def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> list[YTTrack]:
        """Get tracks from a YouTube Music playlist."""
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None,
                partial(self.yt.get_playlist, playlist_id, limit=limit)
            )
            
            tracks = []
            for t in results.get("tracks", []):
                if not t.get("videoId"):
                    continue
                
                artist = "Unknown"
                if t.get("artists") and len(t["artists"]) > 0:
                    artist = t["artists"][0].get("name", "Unknown")
                
                tracks.append(YTTrack(
                    video_id=t["videoId"],
                    title=t.get("title", "Unknown"),
                    artist=artist,
                    duration_seconds=t.get("duration_seconds"),
                ))
            
            return tracks
        except Exception as e:
            logger.error(f"Error getting playlist: {e}")
            return []
    
    async def get_stream_url(self, video_id: str) -> str | None:
        """Get the audio stream URL for a video using yt-dlp."""
        loop = asyncio.get_event_loop()
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            def extract():
                with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info.get("url")
            
            return await loop.run_in_executor(None, extract)
        except Exception as e:
            logger.error(f"Error getting stream URL for {video_id}: {e}")
            return None
    
    async def search_playlists(self, query: str, limit: int = 5) -> list[dict]:
        """Search for playlists."""
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None,
                partial(self.yt.search, query, filter="playlists", limit=limit)
            )
            return [
                {
                    "browse_id": r.get("browseId"),
                    "title": r.get("title"),
                    "author": r.get("author"),
                }
                for r in results if r.get("browseId")
            ]
        except Exception as e:
            logger.error(f"Error searching playlists: {e}")
            return []
    
    def _parse_duration(self, duration_str: str) -> int | None:
        """Parse duration string like '3:45' to seconds."""
        if not duration_str:
            return None
        try:
            parts = duration_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except ValueError:
            pass
        return None
