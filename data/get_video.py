import requests
import asyncio
import io
import youtube_dl
import discord


class Yutube_api:

    def __init__(self):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        self.ffmpeg_options = {
            'options': '-vn',  'before_options': "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"}
        self.http = 'https://www.googleapis.com/youtube/v3'
        self.key = '*'
        self.for_vid = '/videos'
        self.yut_start_url = "https://www.youtube.com/watch?v="
        self.ytdl = youtube_dl.YoutubeDL(ydl_opts)

    async def from_url(self, url, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
        if 'entries' in data:
            data = data['entries']
            players = [Player(discord.FFmpegPCMAudio(
                el['url'], **self.ffmpeg_options, executable='FFmpeg/bin/ffmpeg.exe'), data=el) for el in data]
            return players
        file_name = data['url']
        return Player(discord.FFmpegPCMAudio(file_name, **self.ffmpeg_options, executable='FFmpeg/bin/ffmpeg.exe'), data=data)


class Player(discord.PCMVolumeTransformer):
    def __init__(self, source, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
