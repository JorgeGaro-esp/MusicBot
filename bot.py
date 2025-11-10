import discord
from discord.ext import commands
from config import DISCORD_TOKEN
import asyncio

# Intents necesarios
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print(f"[DEBUG] Mensaje recibido: {message.content} de {message.author}")
    await bot.process_commands(message)

# Lista de cogs a cargar
initial_cogs = ["cogs.music"]

async def main():
    async with bot:
        # Cargar cogs
        for cog in initial_cogs:
            try:
                await bot.load_extension(cog)
                print(f"Cargado: {cog}")
            except Exception as e:
                print(f"Error cargando {cog}: {e}")
        # Iniciar el bot
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido manualmente.")

