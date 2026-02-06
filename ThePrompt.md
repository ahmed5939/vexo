main mission:
- smart discord music bot
- dynamically chooses songs to be played based on the preferences of the users that are in the voice channel
- must throw in songs that the users may not know but will enjoy
- track playback history so to avoid playing the same songs too often
- make use of database for persistent memory, user preferences, song history, etc.
- have a webserver for the bot to show logs, stats, settings, etc.

The final product should be a public bot, published on github, that is easy to setup. There should be instructions also on how to deploy it using docker-compose.





- NORMALIZE SONG TITLE ARTIST TO A SPECIFIC YT LINK (THIS AVOIDS TREATING SIMILAR SONGS AS DIFFERENT ONES)





# Audio Playback Architecture 

### A. The Optimization: `discord.FFmpegOpusAudio`
Instead of decoding audio to PCM (raw waveforms) and re-encoding it, we stream the **Opus** packets directly from YouTube/source to Discord.


### B. yt-dlp Configuration
The `YoutubeDL` instance is configured for low-latency streaming. Critical flags for performance:
- `source_address: 0.0.0.0`: Forces IPv4.
- `format: bestaudio/best`: Gets high quality, but we **must** prioritize Opus/WebM containers to avoid ensuring `FFmpeg` doesn't have to transcode AAC to Opus.

### C. FFmpeg Configuration
Critical flags for stability and passthrough:
```python
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn' # Disable video
}
```

## 2. Playback Management
**File:** `cogs/music.py`

### A. The Async Player Loop
The loop handles the sequential playback and `yt-dlp` spikes:

1.  **Buffered Pre-loading**:
    - The optimized player attempts to "resolve" the next URL (`yt-dlp` extraction) *before* the current song ends if possible.
    - **Optimization**: On RPi 3, this pre-loading is dangerous. It should be done carefully to avoid the 100% CPU spike causing stutter on the *currently playing* track.

2.  **Playing**:
    ```python
    # Optimized: No volume transformer
    source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
    self.vc.play(source, after=lambda e: ...)
    ```

### B. Error Handling & Stutter Mitigation
- **Startup Spikes**: `yt-dlp` launching a Python process is the heaviest operation.
- **Mitigation**: The architecture should effectively "lock" the CPU during this spike. Users may experience 0.5s of stutter on other playing streams when a new one begins. This is a known hardware limitation.

## 3. Required Intents
- `intents.voice_states = True`: Essential for monitoring channel states.



Use @latest_discovery.py as a template for the discovery engine.

Use @latest_digestspotify.py as a template for the digest spotify engine.

probe the api calls from these scripts so that you are aware of the data that you will be working with.

Let's plan the architecture of the bot, database design, user interaction/interface, webserver, user music preferences and anything else that you deem necessary, relevant or cool for the bot to have.


we are only in a planning phase now, so don't write any code yet.

When a plan has been approved, you will providing me with a number of detailed prompts to write the code. It will be up to you to decide how many different ai agents should be used to write the code concurrently.