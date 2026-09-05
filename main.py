import asyncio
import os
import random
from collections import defaultdict
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

# OWNER ROLE ID
OWNER_ROLE_ID = 1525636834233680001

# Veri Depolama (Bellek içi)
user_balances = defaultdict(int)
user_inventories = defaultdict(lambda: defaultdict(int))
user_equipped = defaultdict(lambda: {"olta": None, "yem": None})

# Balık Tanımlamaları: (Ad, Ağırlık/Şans, Fiyat)
FISH_DATA = [
    ("hamsi", 90.0, 10),
    ("çupra", 25.0, 25),
    ("palamut", 10.0, 100),
    ("deniz atı", 7.0, 250),
    ("balon balığı", 5.0, 1000),
    ("kılıç balığı", 3.0, 2500),
    ("köpek balığı", 2.5, 5000),
    ("balina", 1.0, 10000),
    ("megaladon", 0.5, 50000),
]


def catch_fish():
    weights = [f[1] for f in FISH_DATA]
    selected = random.choices(FISH_DATA, weights=weights, k=1)[0]
    return selected[0], selected[2]


@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")


# Custom Cooldown Hata Mesajı
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = round(error.retry_after)
        await ctx.send(
            f"❌ hata bu komutu kullanmak için {seconds} saniye beklemeniz gerekiyor."
        )
    else:
        raise error


# .fish Komutu
@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def fish(ctx):
    await ctx.send("🎣 balık tutuluyor...")
    await asyncio.sleep(5)

    fish_name, price = catch_fish()
    user_id = ctx.author.id

    user_inventories[user_id][fish_name] += 1
    user_balances[user_id] += price

    await ctx.send(f"🪣 kovanıza {fish_name} eklendi.")


# .bakiye Komutu
@bot.command()
async def bakiye(ctx, member: discord.Member = None):
    target = member or ctx.author
    bal = user_balances[target.id]

    embed = discord.Embed(
        title="💰 Bakiye Bilgisi",
        description=f"**{target.mention}** kullanıcısının toplam bakiyesi: **{bal}** bakiye",
        color=discord.Color.gold(),
    )
    await ctx.send(embed=embed)


# .envanter Komutu
@bot.command()
async def envanter(ctx):
    user_id = ctx.author.id
    inv = user_inventories[user_id]
    equipped = user_equipped[user_id]

    embed = discord.Embed(
        title=f"{ctx.author.display_name} kullanıcısının envanteri 🎒",
        color=discord.Color.blue(),
    )

    fish_lines = []
    for name, _, _ in FISH_DATA:
        count = inv[name]
        fish_lines.append(f"• **{name}**: {count}")

    embed.add_field(
        name="🐟 Balıklar", value="\n".join(fish_lines), inline=False
    )

    items_lines = [
        f"• **Süper Olta**: {inv['super_olta']}",
        f"• **Altın Yem**: {inv['altin_yem']}",
    ]
    embed.add_field(
        name="🎒 Eşyalar", value="\n".join(items_lines), inline=False
    )

    active_lines = [
        f"• **Aktif Olta**: {equipped['olta'] or 'Yok'}",
        f"• **Aktif Yem**: {equipped['yem'] or 'Yok'}",
    ]
    embed.add_field(
        name="⚙️ Takılı Ekipmanlar",
        value="\n".join(active_lines),
        inline=False,
    )

    await ctx.send(embed=embed)


# .bakiyeekle Komutu
@bot.command()
async def bakiyeekle(ctx, member: discord.Member, miktar: int):
    has_role = any(role.id == OWNER_ROLE_ID for role in ctx.author.roles)
    if not has_role:
        await ctx.send("❌ hata bu komutu sadece ownerler kullanabilir.")
        return

    user_balances[member.id] += miktar
    yeni_bakiye = user_balances[member.id]
    await ctx.send(
        f"{member.mention} kullanıcısına {miktar} bakiye eklendi şu anda mevcut bakiyesi :\n{yeni_bakiye}"
    )


# .magaza Komutu
@bot.command()
async def magaza(ctx):
    embed = discord.Embed(
        title="🛒 Balıkçılık Mağazası", color=discord.Color.green()
    )
    embed.add_field(
        name="🎣 Süper Olta",
        value="Fiyat: **100000** Bakiye\nSatın Al: `.al super_olta`",
        inline=False,
    )
    embed.add_field(
        name="🪱 Altın Yem",
        value="Fiyat: **5000** Bakiye\nSatın Al: `.al altin_yem`",
        inline=False,
    )
    await ctx.send(embed=embed)


# Satın Alma Komutu (.al)
@bot.command()
async def al(ctx, esya: str):
    user_id = ctx.author.id
    bal = user_balances[user_id]
    esya = esya.lower()

    if esya in ["super_olta", "süper olta", "superolta"]:
        if bal < 100000:
            await ctx.send("❌ hata süper olta almak için 100000 bakiyesi gerekir.")
            return
        user_balances[user_id] -= 100000
        user_inventories[user_id]["super_olta"] += 1
        await ctx.send(
            "✅ süper olta başarılı bir şekilde alındı .oltakullan yazarak süper oltayı kullanabilirsin."
        )

    elif esya in ["altin_yem", "altın yem", "altinyem"]:
        if bal < 5000:
            await ctx.send("❌ hata altın yem almak için 5000 bakiye gerekir.")
            return
        user_balances[user_id] -= 5000
        user_inventories[user_id]["altin_yem"] += 1
        await ctx.send(
            "✅ altın yem başarılı bir şekilde alındı .yemkullan yazarak altın yemi kullanabilirsin."
        )
    else:
        await ctx.send(
            "❌ Geçersiz eşya adı. Kullanım: `.al super_olta` veya `.al altin_yem`"
        )


# .oltakullan Komutu
@bot.command()
async def oltakullan(ctx):
    user_id = ctx.author.id
    if user_inventories[user_id]["super_olta"] < 1:
        await ctx.send("❌ Envanterinizde Süper Olta bulunmuyor.")
        return
    user_equipped[user_id]["olta"] = "Süper Olta"
    await ctx.send("✅ Süper Olta başarıyla takıldı!")


# .oltaçıkart Komutu
@bot.command()
async def oltaçıkart(ctx):
    user_id = ctx.author.id
    if not user_equipped[user_id]["olta"]:
        await ctx.send("❌ Zaten takılı bir oltanız yok.")
        return
    user_equipped[user_id]["olta"] = None
    await ctx.send("✅ Olta başarıyla çıkartıldı.")


# .yemkullan Komutu
@bot.command()
async def yemkullan(ctx):
    user_id = ctx.author.id
    if user_inventories[user_id]["altin_yem"] < 1:
        await ctx.send("❌ Envanterinizde Altın Yem bulunmuyor.")
        return
    user_equipped[user_id]["yem"] = "Altın Yem"
    await ctx.send("✅ Altın Yem başarıyla takıldı!")


# .yemçıkart Komutu
@bot.command()
async def yemçıkart(ctx):
    user_id = ctx.author.id
    if not user_equipped[user_id]["yem"]:
        await ctx.send("❌ Zaten takılı bir yeminiz yok.")
        return
    user_equipped[user_id]["yem"] = None
    await ctx.send("✅ Yem başarıyla çıkartıldı.")


# .yardım Komutu
@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="📜 Bot Komut Menüsü",
        description="Aşağıda bot içerisinde kullanabileceğiniz tüm komutlar yer almaktadır:",
        color=discord.Color.purple(),
    )
    embed.add_field(
        name="🎣 Balıkçılık Komutları",
        value="`.fish` - 5 saniye bekleyip şansa göre balık tutar (10sn cooldown).\n"
              "`.envanter` - Tuttuğunuz balıkları ve eşyalarınızı gösterir.",
        inline=False,
    )
    embed.add_field(
        name="💰 Bakiye ve Mağaza Komutları",
        value="`.bakiye` - Bakiyenizi görüntüler.\n"
              "`.magaza` - Satın alınabilir eşyaları listeler.\n"
              "`.al <eşya_adı>` - Mağazadan eşya satın alır.",
        inline=False,
    )
    embed.add_field(
        name="⚙️ Ekipman Komutları",
        value="`.oltakullan` / `.oltaçıkart` - Süper oltayı takar veya çıkarır.\n"
              "`.yemkullan` / `.yemçıkart` - Altın yemi takar veya çıkarır.",
        inline=False,
    )
    embed.add_field(
        name="👑 Yönetici Komutları",
        value="`.bakiyeekle @kullanıcı <miktar>` - Kullanıcıya bakiye ekler (Sadece yetkili rol).",
        inline=False,
    )
    await ctx.send(embed=embed)


token = os.getenv("BOT_TOKEN")
bot.run(token)
