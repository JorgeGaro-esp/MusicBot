import discord
from discord.ext import commands
import asyncio
import re
from config import FFMPEG_OPTIONS
from .utils import search_youtube, get_spotify_tracks

queues = {}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in queues or not queues[guild_id]:
            await ctx.voice_client.disconnect()
            return
        url, title = queues[guild_id].pop(0)
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        await ctx.send(f"🎵 Reproduciendo ahora: **{title}**")

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f"Conectado a **{channel}**")
        else:
            await ctx.send("Tienes que estar en un canal de voz primero.")

    @commands.command()
    async def play(self, ctx, *, query: str):
        guild_id = ctx.guild.id
        if ctx.voice_client is None:
            await self.join(ctx)

        if re.match(r"https?://open\.spotify\.com", query):
            tracks = await get_spotify_tracks(query)
            await ctx.send(f"🎧 Añadiendo {len(tracks)} canciones desde Spotify...")
            for t in tracks:
                url, title = await search_youtube(t)
                queues.setdefault(guild_id, []).append((url, title))
        else:
            if "youtube.com" in query or "youtu.be" in query:
                info = await search_youtube(query)
                url, title = info
            else:
                url, title = await search_youtube(query)
            queues.setdefault(guild_id, []).append((url, title))
            await ctx.send(f"✅ Añadido a la cola: **{title}**")

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Canción saltada.")

    @commands.command()
    async def queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in queues or not queues[guild_id]:
            await ctx.send("🪣 La cola está vacía.")
        else:
            msg = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(queues[guild_id])])
            await ctx.send(f"🎶 **Cola actual:**\n{msg}")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Pausado.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Reanudado.")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            queues[ctx.guild.id] = []
            ctx.voice_client.stop()
            await ctx.send("🛑 Música detenida y cola vacía.")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Desconectado.")

def setup(bot):
    bot.add_cog(Music(bot))
