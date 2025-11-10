import discord
from discord.ext import commands
import asyncio
import re
from discord import FFmpegPCMAudio
from .utils import search_youtube, get_spotify_tracks
from config import FFMPEG_OPTIONS
import yt_dlp  # 🔹 Nuevo: para extraer el stream de audio real

queues = {}  # Cola por servidor


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in queues or not queues[guild_id]:
            print(f"[DEBUG] Cola vacía en guild {ctx.guild.name}. Desconectando...")
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            return

        url, title = queues[guild_id].pop(0)
        print(f"[DEBUG] Reproduciendo: {title} -> {url}")

        try:
            # 🔹 Configuración de yt_dlp para obtener el enlace de audio directo
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "default_search": "auto",
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info["url"]

            source = FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)

            # ✅ Usa run_coroutine_threadsafe para evitar el warning
            ctx.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                ),
            )

            await ctx.send(f"🎵 Reproduciendo ahora: **{title}**")

        except Exception as e:
            print(f"[ERROR] No se pudo reproducir {title}: {e}")
            await ctx.send(f"❌ Error reproduciendo {title}")

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            try:
                await channel.connect()
                print(f"[DEBUG] Conectado a canal: {channel.name}")
                await ctx.send(f"✅ Conectado a **{channel}**")
            except Exception as e:
                print(f"[ERROR] No se pudo unir al canal: {e}")
                await ctx.send(f"❌ No pude unirme al canal: {e}")
        else:
            print("[DEBUG] Usuario no está en canal de voz")
            await ctx.send("⚠️ Tienes que estar en un canal de voz primero.")

    @commands.command()
    async def play(self, ctx, *, query: str):
        print(f"[DEBUG] Comando !play recibido: {query}")
        guild_id = ctx.guild.id

        if ctx.voice_client is None:
            print("[DEBUG] Bot no conectado, intentando join automático...")
            await self.join(ctx)
            if ctx.voice_client is None:
                print("[ERROR] Bot no se pudo conectar al canal de voz.")
                await ctx.send("❌ No estoy en un canal de voz y no pude unirme.")
                return

        # Detectar Spotify
        if re.match(r"https?://open\.spotify\.com", query):
            try:
                tracks = await get_spotify_tracks(query)
                await ctx.send(f"🎧 Añadiendo {len(tracks)} canciones desde Spotify...")
                print(f"[DEBUG] Tracks de Spotify: {tracks}")
                for t in tracks:
                    url, title = await search_youtube(t)
                    queues.setdefault(guild_id, []).append((url, title))
                    print(f"[DEBUG] Añadido a cola: {title} -> {url}")
            except Exception as e:
                print(f"[ERROR] Error al obtener tracks de Spotify: {e}")
                await ctx.send(f"❌ Error obteniendo canciones de Spotify: {e}")
        else:
            try:
                url, title = await search_youtube(query)
                queues.setdefault(guild_id, []).append((url, title))
                print(f"[DEBUG] Añadido a cola: {title} -> {url}")
                await ctx.send(f"✅ Añadido a la cola: **{title}**")
            except Exception as e:
                print(f"[ERROR] Error buscando en YouTube: {e}")
                await ctx.send(f"❌ Error buscando canción: {e}")

        if not ctx.voice_client.is_playing():
            print("[DEBUG] Iniciando reproducción...")
            await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            print("[DEBUG] Canción saltada.")
            ctx.voice_client.stop()
            await ctx.send("⏭️ Canción saltada.")
        else:
            print("[DEBUG] No hay canción para saltar.")
            await ctx.send("⚠️ No hay canción reproduciéndose.")

    @commands.command()
    async def queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in queues or not queues[guild_id]:
            print("[DEBUG] Cola vacía.")
            await ctx.send("🪣 La cola está vacía.")
        else:
            msg = "\n".join(
                [f"{i+1}. {title}" for i, (_, title) in enumerate(queues[guild_id])]
            )
            print(f"[DEBUG] Cola actual:\n{msg}")
            await ctx.send(f"🎶 **Cola actual:**\n{msg}")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            print("[DEBUG] Música pausada.")
            await ctx.send("⏸️ Pausado.")
        else:
            print("[DEBUG] No hay música reproduciéndose para pausar.")
            await ctx.send("⚠️ No hay música reproduciéndose.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            print("[DEBUG] Música reanudada.")
            await ctx.send("▶️ Reanudado.")
        else:
            print("[DEBUG] No hay música pausada para reanudar.")
            await ctx.send("⚠️ No hay música pausada.")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            queues[ctx.guild.id] = []
            ctx.voice_client.stop()
            print("[DEBUG] Música detenida y cola vacía.")
            await ctx.send("🛑 Música detenida y cola vacía.")
        else:
            print("[DEBUG] Bot no está en un canal de voz para detener música.")
            await ctx.send("⚠️ No estoy en un canal de voz.")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            print("[DEBUG] Bot desconectado del canal de voz.")
            await ctx.send("👋 Desconectado.")
        else:
            print("[DEBUG] Bot no está en un canal de voz para desconectarse.")
            await ctx.send("⚠️ No estoy en un canal de voz.")


# Exportar cog correctamente
async def setup(bot):
    await bot.add_cog(Music(bot))

