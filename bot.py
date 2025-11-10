import discord
from discord.ext import commands
from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# Cargar Cogs automáticamente
initial_cogs = ["cogs.music"]
for cog in initial_cogs:
    try:
        bot.load_extension(cog)
        print(f"Cargado: {cog}")
    except Exception as e:
        print(f"Error cargando {cog}: {e}")

bot.run(DISCORD_TOKEN)
