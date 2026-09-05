import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

# Web sunucusu (7/24 aktif kalması için)
app = Flask('')

@app.route('/')
def home():
    return "Bot 7/24 Aktif!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Discord Bot Ayarları
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} başarıyla giriş yaptı!")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# Web sunucusunu başlat
keep_alive()

# Bot Token'ı Render'dan alınacak
bot.run(os.getenv("BOT_TOKEN"))
