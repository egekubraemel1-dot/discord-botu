import asyncio
import os
import random
from collections import defaultdict
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

# Prefix a! Olarak Ayarlandı
bot = commands.Bot(command_prefix="a!", intents=intents, help_command=None)

# SABİT TANIMLAMALAR
OWNER_ROLE_ID = 1525636834233680001

# Veri Depolama (Bellek İçi)
user_balances = defaultdict(int)
user_inventories = defaultdict(lambda: defaultdict(int))
user_equipped = defaultdict(lambda: {"olta": None, "yem": None})

# Balık Fiyatları
FISH_PRICES = {
    "hamsi": 10,
    "çupra": 25,
    "palamut": 100,
    "deniz atı": 250,
    "balon balığı": 1000,
    "kılıç balığı": 2500,
    "köpek balığı": 5000,
    "balina": 10000,
    "megaladon": 50000,
}

# Şans Oranları
BASE_RATES = [
    ("hamsi", 90.0),
    ("çupra", 25.0),
    ("palamut", 10.0),
    ("deniz atı", 7.0),
    ("balon balığı", 5.0),
    ("kılıç balığı", 3.0),
    ("köpek balığı", 2.5),
    ("balina", 1.0),
    ("megaladon", 0.5),
]

YEM_RATES = [
    ("hamsi", 89.0),
    ("çupra", 26.0),
    ("palamut", 11.0),
    ("deniz atı", 7.5),
    ("balon balığı", 5.5),
    ("kılıç balığı", 3.25),
    ("köpek balığı", 2.7),
    ("balina", 1.05),
    ("megaladon", 0.51),
]

OLTA_RATES = [
    ("hamsi", 85.0),
    ("çupra", 30.0),
    ("palamut", 12.0),
    ("deniz atı", 8.5),
    ("balon balığı", 6.0),
    ("kılıç balığı", 4.0),
    ("köpek balığı", 3.0),
    ("balina", 1.25),
    ("megaladon", 0.6),
]


def catch_fish(user_id):
    equipped = user_equipped[user_id]

    if equipped["olta"] == "Süper Olta":
        active_rates = OLTA_RATES
    elif equipped["yem"] == "Altın Yem":
        active_rates = YEM_RATES
    else:
        active_rates = BASE_RATES

    names = [f[0] for f in active_rates]
    weights = [f[1] for f in active_rates]

    selected_fish = random.choices(names, weights=weights, k=1)[0]
    return selected_fish


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=".gg/apexis"))
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} Adet Slash Komutu Senkronize Edildi.")
    except Exception as e:
        print(f"Slash Komutu Senkronizasyon Hatası: {e}")
    print(f"{bot.user} Olarak Giriş Yapıldı!")


# Otomatik Selamlama Ve Hızlı Cevap
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip().lower() == "sa":
        await message.channel.send("Aleyküm Selam Hoşgeldin.")

    await bot.process_commands(message)


# Custom Cooldown Hata Mesajı
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = round(error.retry_after)
        await ctx.send(
            f"**❌ | Bu Komutu Tekrar Kullanabilmek İçin {seconds} Saniye Beklemeniz Gerekmektedir.**"
        )
    else:
        raise error


# a!fish Komutu
@bot.command(aliases=["fısh", "baliklar", "tut"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def fish(ctx):
    msg = await ctx.send("**🎣 | Balık Tutuluyor...**")
    await asyncio.sleep(5)

    user_id = ctx.author.id
    fish_name = catch_fish(user_id)

    user_inventories[user_id][fish_name] += 1

    await msg.edit(content=f"**🪣 | Kovanıza {fish_name.title()} Eklendi.**")


# a!sat Komutu
@bot.command(aliases=["satış", "satis"])
async def sat(ctx):
    user_id = ctx.author.id
    inv = user_inventories[user_id]

    total_earnings = 0
    sold_count = 0

    for fish_name, price in FISH_PRICES.items():
        count = inv[fish_name]
        if count > 0:
            total_earnings += count * price
            sold_count += count
            inv[fish_name] = 0

    if sold_count == 0:
        await ctx.send(
            "**❌ | Envanterinde Henüz Balık Yok a!fish Yazarak Balık Tutmaya Başla.**"
        )
        return

    user_balances[user_id] += total_earnings

    await ctx.send(
        f"**✅ | Başarılı Bir Şekilde Envanterinde Bulunan Balıklar Satıldı. Yeni Bakiyen {user_balances[user_id]} Olmuştur.**"
    )


# a!balık Komutu
@bot.command(aliases=["balıklar", "balik", "fishlist"])
async def balık(ctx):
    fish_list = (
        "**Hamsi**\n"
        "**Çupra**\n"
        "**Palamut**\n"
        "**Deniz Atı**\n"
        "**Balon Balığı**\n"
        "**Kılıç Balığı**\n"
        "**Köpek Balığı**\n"
        "**Balina**\n"
        "**Megaladon**"
    )

    embed = discord.Embed(
        title="**🐟 Balık Listesi**",
        description=fish_list,
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed)


# a!fiyat Komutu
@bot.command(aliases=["fiyati", "fiyatı", "price"])
async def fiyat(ctx, *, balık_adı: str = None):
    if not balık_adı:
        await ctx.send(
            "**❌ | Lütfen Fiyatını Öğrenmek İstediğiniz Balığın Adını Yazınız. Örnek: `a!fiyat hamsi`**"
        )
        return

    normalized_name = balık_adı.lower().strip()

    if normalized_name in FISH_PRICES:
        price = FISH_PRICES[normalized_name]
        formatted_name = normalized_name.title()

        embed = discord.Embed(
            description=f"**🐟 | {formatted_name} Fiyatı {price} Bakiyedir.**",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(
            "**❌ | Belirtilen İsimde Bir Balık Bulunamadı. `a!balık` Yazarak Tüm Balıkları Görebilirsiniz.**"
        )


# a!bakiye Komutu
@bot.command(aliases=["bakıye", "para", "balance"])
async def bakiye(ctx, member: discord.Member = None):
    target = member or ctx.author
    bal = user_balances[target.id]

    embed = discord.Embed(
        title="**💰 Bakiye Bilgisi**",
        description=f"**{target.mention} Kullanıcısının Mevcut Bakiyesi:** **{bal}**",
        color=discord.Color.gold(),
    )
    await ctx.send(embed=embed)


# a!envanter Komutu
@bot.command(aliases=["inv", "inventory"])
async def envanter(ctx):
    user_id = ctx.author.id
    inv = user_inventories[user_id]
    equipped = user_equipped[user_id]

    embed = discord.Embed(
        title=f"**🎒 {ctx.author.display_name} Envanteri**",
        color=discord.Color.blue(),
    )

    fish_lines = []
    for name in FISH_PRICES.keys():
        count = inv[name]
        fish_lines.append(f"• **{name.title()}**: **{count}**")

    embed.add_field(
        name="**🐟 Balıklar**", value="\n".join(fish_lines), inline=False
    )

    items_lines = [
        f"• **Süper Olta**: **{inv['super_olta']}**",
        f"• **Altın Yem**: **{inv['altin_yem']}**",
    ]
    embed.add_field(
        name="**🎒 Eşyalar**", value="\n".join(items_lines), inline=False
    )

    active_lines = [
        f"• **Aktif Olta**: **{equipped['olta'] or 'Yok'}**",
        f"• **Aktif Yem**: **{equipped['yem'] or 'Yok'}**",
    ]
    embed.add_field(
        name="**⚙️ Takılı Ekipmanlar**",
        value="\n".join(active_lines),
        inline=False,
    )

    await ctx.send(embed=embed)


# a!bakiyeekle Komutu
@bot.command(aliases=["bakıyeekle", "paraekle"])
async def bakiyeekle(ctx, member: discord.Member, miktar: int):
    has_role = any(role.id == OWNER_ROLE_ID for role in ctx.author.roles)
    if not has_role:
        await ctx.send(
            "**❌ | Bu Komutu Kullanmak İçin Gerekli Yetkiye Sahip Değilsiniz.**"
        )
        return

    user_balances[member.id] += miktar
    yeni_bakiye = user_balances[member.id]
    await ctx.send(
        f"**✅ | Başarılı Bir Şekilde {member.mention} Kullanıcısına {miktar} Bakiye Eklendi. Yeni Bakiyesi: {yeni_bakiye}**"
    )


# a!bakiyesil Komutu
@bot.command(aliases=["bakıyesil", "parasil"])
async def bakiyesil(ctx, member: discord.Member, miktar: int):
    has_role = any(role.id == OWNER_ROLE_ID for role in ctx.author.roles)
    if not has_role:
        await ctx.send(
            "**❌ | Bu Komutu Kullanmak İçin Gerekli Yetkiye Sahip Değilsiniz.**"
        )
        return

    user_balances[member.id] -= miktar
    yeni_bakiye = user_balances[member.id]
    await ctx.send(
        f"**✅ | Başarılı Bir Şekilde {member.mention} Kullanıcısından {miktar} Bakiye Silinmiştir Yeni Bakiyesi {yeni_bakiye} Olmuştur.**"
    )


# a!magaza Komutu
@bot.command(aliases=["mağaza", "shop", "store"])
async def magaza(ctx):
    embed = discord.Embed(
        title="**🛒 Balıkçılık Mağazası**", color=discord.Color.green()
    )
    embed.add_field(
        name="**🎣 Süper Olta**",
        value="**Fiyat:** **100000** Bakiye\n**Satın Al:** **`a!al super_olta`**",
        inline=False,
    )
    embed.add_field(
        name="**🪱 Altın Yem**",
        value="**Fiyat:** **5000** Bakiye\n**Satın Al:** **`a!al altin_yem`**",
        inline=False,
    )
    await ctx.send(embed=embed)


# a!al Komutu
@bot.command(aliases=["buy", "satınal", "satinal"])
async def al(ctx, *, esya: str):
    user_id = ctx.author.id
    bal = user_balances[user_id]
    esya = esya.lower()

    if esya in ["super_olta", "süper olta", "superolta"]:
        if bal < 100000:
            await ctx.send(
                "**❌ | Süper Olta Satın Almak İçin 100000 Bakiyeniz Olması Gerekmektedir.**"
            )
            return
        user_balances[user_id] -= 100000
        user_inventories[user_id]["super_olta"] += 1
        await ctx.send(
            "**✅ | Süper Olta Başarılı Bir Şekilde Satın Alındı. a!oltakullan Yazarak Kuşanabilirsiniz.**"
        )

    elif esya in ["altin_yem", "altın yem", "altinyem"]:
        if bal < 5000:
            await ctx.send(
                "**❌ | Altın Yem Satın Almak İçin 5000 Bakiyeniz Olması Gerekmektedir.**"
            )
            return
        user_balances[user_id] -= 5000
        user_inventories[user_id]["altin_yem"] += 1
        await ctx.send(
            "**✅ | Altın Yem Başarılı Bir Şekilde Satın Alındı. a!yemkullan Yazarak Kuşanabilirsiniz.**"
        )
    else:
        await ctx.send(
            "**❌ | Geçersiz Eşya Adı. Kullanım: a!al super_olta Veya a!al altin_yem**"
        )


# Ekipman Kullanım Komutları
@bot.command(aliases=["oltakullanım", "oltatak"])
async def oltakullan(ctx):
    user_id = ctx.author.id
    if user_inventories[user_id]["super_olta"] < 1:
        await ctx.send("**❌ | Envanterinizde Süper Olta Bulunmamaktadır.**")
        return
    user_equipped[user_id]["olta"] = "Süper Olta"
    await ctx.send("**✅ | Süper Olta Başarıyla Takıldı.**")


@bot.command(aliases=["oltacıkart", "oltacikar"])
async def oltaçıkart(ctx):
    user_id = ctx.author.id
    if not user_equipped[user_id]["olta"]:
        await ctx.send("**❌ | Takılı Bir Oltanız Bulunmamaktadır.**")
        return
    user_equipped[user_id]["olta"] = None
    await ctx.send("**✅ | Olta Başarıyla Çıkartıldı.**")


@bot.command(aliases=["yemkullanım", "yemtak"])
async def yemkullan(ctx):
    user_id = ctx.author.id
    if user_inventories[user_id]["altin_yem"] < 1:
        await ctx.send("**❌ | Envanterinizde Altın Yem Bulunmamaktadır.**")
        return
    user_equipped[user_id]["yem"] = "Altın Yem"
    await ctx.send("**✅ | Altın Yem Başarıyla Takıldı.**")


@bot.command(aliases=["yemcıkart", "yemcikar"])
async def yemçıkart(ctx):
    user_id = ctx.author.id
    if not user_equipped[user_id]["yem"]:
        await ctx.send("**❌ | Takılı Bir Yeminiz Bulunmamaktadır.**")
        return
    user_equipped[user_id]["yem"] = None
    await ctx.send("**✅ | Yem Başarıyla Çıkartıldı.**")


# Kompakt Yardım Embed Oluşturucu
def get_help_embed():
    embed = discord.Embed(color=discord.Color.blue())

    embed.add_field(
        name="🎣 Balıkçılık",
        value="`a!fish` `a!sat` `a!envanter` `a!balık` `a!fiyat`",
        inline=False,
    )
    embed.add_field(
        name="💰 Ekonomi",
        value="`a!bakiye` `a!magaza`",
        inline=False,
    )
    embed.add_field(
        name="⚙️ Ekipman",
        value="`a!oltakullan` `a!oltaçıkart` `a!yemkullan` `a!yemçıkart`",
        inline=False,
    )
    embed.add_field(
        name="👑 Yönetici",
        value="`a!bakiyeekle` `a!bakiyesil`",
        inline=False,
    )
    return embed


# a!yardım Komutu
@bot.command(aliases=["yardim", "help"])
async def yardım(ctx):
    await ctx.send(embed=get_help_embed())


# /yardım ve /yardim Slash Komutları
@bot.tree.command(name="yardım", description="Bot Komut Menüsünü Gösterir.")
async def slash_yardim(interaction: discord.Interaction):
    await interaction.response.send_message(embed=get_help_embed())


@bot.tree.command(name="yardim", description="Bot Komut Menüsünü Gösterir.")
async def slash_yardim_tr(interaction: discord.Interaction):
    await interaction.response.send_message(embed=get_help_embed())


token = os.getenv("BOT_TOKEN")
bot.run(token)
