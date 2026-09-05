import os
import discord
from discord.ext import commands

# Bot izinlerini ayarlıyoruz
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")


# Komut örneği: !ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")


# Mesaj dinleyici: SA yanıtı
@bot.event
async def on_message(message):
    # Botun kendi mesajlarına yanıt vermesini engeller
    if message.author == bot.user:
        return

    # "sa", "Sa" veya "SA" yazıldığında yanıt verir
    if message.content.lower() == "sa":
        await message.channel.send("Aleyküm Selam Hoşgeldin.")

    # !ping gibi diğer komutların aksamadan çalışmasını sağlar
    await bot.process_commands(message)


# Token'ı çevre değişkeninden çeker
token = os.getenv("BOT_TOKEN")
bot.run(token)
