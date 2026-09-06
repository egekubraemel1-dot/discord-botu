import asyncio
import os
import random
from collections import defaultdict
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Prefix a! Ve a. Olarak Ayarlandı
bot = commands.Bot(command_prefix=["a!", "a."], intents=intents, help_command=None)

# SABİT TANIMLAMALAR
OWNER_ROLE_ID = 1525636834233680001

# Veri Depolama (Bellek İçi)
user_balances = defaultdict(int)
user_inventories = defaultdict(lambda: defaultdict(int))
user_equipped = defaultdict(lambda: {"olta": None, "yem": None})

# Balık Verileri (Fiyat, Şans Ve Emojiler)
FISH_DATA = {
    "hamsi": {"price": 10, "chance": 85.0, "emoji": "🐟"},
    "çupra": {"price": 50, "chance": 20.0, "emoji": "🐠"},
    "palamut": {"price": 120, "chance": 10.0, "emoji": "🎣"},
    "deniz atı": {"price": 250, "chance": 7.5, "emoji": "🌊"},
    "balon balığı": {"price": 500, "chance": 5.0, "emoji": "🐡"},
    "kılıç balığı": {"price": 1200, "chance": 2.5, "emoji": "🗡️"},
    "köpek balığı": {"price": 3000, "chance": 1.0, "emoji": "🦈"},
    "balina": {"price": 8000, "chance": 0.5, "emoji": "🐋"},
    "megaladon": {"price": 25000, "chance": 0.2, "emoji": "🐙"}
}

def catch_fish(user_id):
    equipped = user_equipped[user_id]
    
    # Ekipman Bonusları
    chance_multiplier = 1.0
    if equipped["olta"] == "Süper Olta":
        chance_multiplier = 1.2
    elif equipped["yem"] == "Altın Yem":
        chance_multiplier = 1.1

    caught_fish = []
    for name, data in FISH_DATA.items():
        adjusted_chance = min(100.0, data["chance"] * chance_multiplier)
        if random.uniform(0, 100) <= adjusted_chance:
            caught_fish.append(name)

    if not caught_fish:
        return None

    return random.choice(caught_fish)

# Butonlu Ve Kategorili Satış Arayüzü
class SellAmountView(discord.ui.View):
    def __init__(self, user_id, fish_name):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.fish_name = fish_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("** ❌ | Bu İşlemi Sadece Komutu Kullanan Kişi Yapabilir. **", ephemeral=True)
            return False
        return True

    async def process_sale(self, interaction: discord.Interaction, amount: int):
        inv = user_inventories[self.user_id]
        current_owned = inv[self.fish_name]

        if amount == -1:  # Hepsini Sat
            amount = current_owned

        formatted_fish = self.fish_name.title()

        if current_owned < amount or amount <= 0:
            needed = amount - current_owned
            await interaction.response.send_message(
                f"** ❌ | Hata {amount} Satmak İçin {needed} Daha {formatted_fish} Gereklidir. **",
                ephemeral=True
            )
            return

        price_per_unit = FISH_DATA[self.fish_name]["price"]
        total_earnings = amount * price_per_unit
        
        inv[self.fish_name] -= amount
        user_balances[self.user_id] += total_earnings
        new_bal = user_balances[self.user_id]

        await interaction.response.send_message(
            f"** ✅ | Başarılı Bir Şekilde {amount} Tane {formatted_fish} Satıldı. Yeni Bakiyen {new_bal} Olmuştur. **"
        )
        self.stop()

    @discord.ui.button(label="1 Tane Sat", style=discord.ButtonStyle.primary)
    async def sell_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_sale(interaction, 1)

    @discord.ui.button(label="3 Tane Sat", style=discord.ButtonStyle.primary)
    async def sell_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_sale(interaction, 3)

    @discord.ui.button(label="5 Tane Sat", style=discord.ButtonStyle.primary)
    async def sell_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_sale(interaction, 5)

    @discord.ui.button(label="Hepsini Sat", style=discord.ButtonStyle.success)
    async def sell_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_sale(interaction, -1)

class FishCategorySelect(discord.ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label=f"{data['emoji']} {fish.title()}",
                value=fish,
                description=f"Fiyat: {data['price']} Bakiye"
            )
            for fish, data in FISH_DATA.items()
        ]
        super().__init__(placeholder="Satmak İstediğin Balık Türünü Seç...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("** ❌ | Bu İşlemi Sadece Komutu Kullanan Kişi Yapabilir. **", ephemeral=True)
            return
        
        selected_fish = self.values[0]
        view = SellAmountView(self.user_id, selected_fish)
        await interaction.response.send_message(
            f"** 🎣 | {selected_fish.title()} İçin Kaç Tane Satmak İstediğini Seç: **",
            view=view,
            ephemeral=True
        )

class SellCategoryView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(FishCategorySelect(user_id))

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=".gg/apexis"))
    try:
        synced = await bot.tree.sync()
        print(f"** {len(synced)} Adet Slash Komutu Senkronize Edildi. **")
    except Exception as e:
        print(f"** Slash Komutu Senkronizasyon Hatası: {e} **")
    print(f"** {bot.user} Olarak Giriş Yapıldı! **")

# Otomatik Selamlama Ve Hızlı Cevap Trigger
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip().lower()
    if content in ["sa", "s.a", "s.a.", "selam", "selamunaleykum", "selamün aleyküm"]:
        await message.channel.send(f"** 🖐️ | Aleykümselam {message.author.mention}, Hoş Geldin! **")

    await bot.process_commands(message)

# Cooldown Hata Mesajı
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = round(error.retry_after)
        await ctx.send(
            f"** ❌ | Bu Komutu Tekrar Kullanabilmek İçin {seconds} Saniye Beklemeniz Gerekmektedir. **"
        )
    else:
        raise error

# 1) Balık Tutma Komutu (a!fish, a!tut, a!balıktut)
@bot.command(aliases=["tut", "balıktut", "balıkayık"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def fish(ctx):
    msg = await ctx.send("** 🎣 | Balık Tutuluyor... **")
    await asyncio.sleep(3)

    user_id = ctx.author.id
    fish_name = catch_fish(user_id)

    if not fish_name:
        await msg.edit(content=f"** 🎣 | Maalesef {ctx.author.mention}, Olta Boş Çıktı! **")
        return

    user_inventories[user_id][fish_name] += 1
    emoji = FISH_DATA[fish_name]["emoji"]

    await msg.edit(content=f"** 🪣 | Kovanıza {emoji} {fish_name.title()} Eklendi. **")

# 2) Satış Komutu (a!sat, a!satış, a!satis)
@bot.command(aliases=["satış", "satis"])
async def sat(ctx):
    view = SellCategoryView(ctx.author.id)
    await ctx.send(f"** 🛒 | {ctx.author.mention}, Satmak İstediğin Balık Kategorisini Seç: **", view=view)

# 3) Balık Listesi Komutu (a!balık, a!baliklar, a!fishlist)
@bot.command(name="balık", aliases=["baliklar", "fishlist"])
async def balık_listesi(ctx):
    fish_list = "\n".join([f"** {data['emoji']} {name.title()} **" for name, data in FISH_DATA.items()])

    embed = discord.Embed(
        title="** 🐟 | Balık Listesi **",
        description=fish_list,
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed)

# 4) Fiyat Öğrenme Komutu
@bot.command(aliases=["fıyat", "fiyati", "fiyatı", "price", "fiyatlar", "fıyatlar"])
async def fiyat(ctx, *, balık_adı: str = None):
    if not balık_adı:
        embed = discord.Embed(title="** 📊 | Balık Fiyat Listesi **", color=discord.Color.blue())
        for name, data in FISH_DATA.items():
            embed.add_field(
                name=f"{data['emoji']} {name.title()}",
                value=f"** Fiyat: {data['price']} Bakiye **\n** Şans: %{data['chance']} **",
                inline=True
            )
        await ctx.send(embed=embed)
        return

    normalized_name = balık_adı.lower().strip()

    if normalized_name in FISH_DATA:
        data = FISH_DATA[normalized_name]
        formatted_name = normalized_name.title()

        embed = discord.Embed(
            description=f"** {data['emoji']} | {formatted_name} Fiyatı {data['price']} Bakiyedir. (Şans: %{data['chance']}) **",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(
            "** ❌ | Belirtilen İsimde Bir Balık Bulunamadı. `a!balık` Yazarak Tüm Balıkları Görebilirsiniz. **"
        )

# 5) Bakiye Komutu
@bot.command(aliases=["bakıye", "para", "balance", "cüzdan", "cuzdan"])
async def bakiye(ctx, member: discord.Member = None):
    target = member or ctx.author
    bal = user_balances[target.id]

    embed = discord.Embed(
        title="** 💰 | Bakiye Bilgisi **",
        description=f"** {target.mention} Kullanıcısının Mevcut Bakiyesi: {bal} Bakiye **",
        color=discord.Color.gold(),
    )
    await ctx.send(embed=embed)

# 6) Envanter Komutu
@bot.command(aliases=["inv", "inventory", "çanta", "canta"])
async def envanter(ctx):
    user_id = ctx.author.id
    inv = user_inventories[user_id]
    equipped = user_equipped[user_id]

    embed = discord.Embed(
        title=f"** 🎒 | {ctx.author.display_name} Envanteri **",
        color=discord.Color.blue(),
    )

    fish_lines = []
    for name, data in FISH_DATA.items():
        count = inv[name]
        fish_lines.append(f"• **{data['emoji']} {name.title()}**: **{count}**")

    embed.add_field(
        name="** 🐟 | Balıklar **", value="\n".join(fish_lines), inline=False
    )

    items_lines = [
        f"• **🎣 Süper Olta**: **{inv['super_olta']}**",
        f"• **🪱 Altın Yem**: **{inv['altin_yem']}**",
    ]
    embed.add_field(
        name="** 🎒 | Eşyalar **", value="\n".join(items_lines), inline=False
    )

    active_lines = [
        f"• **Aktif Olta**: **{equipped['olta'] or 'Yok'}**",
        f"• **Aktif Yem**: **{equipped['yem'] or 'Yok'}**",
    ]
    embed.add_field(
        name="** ⚙️ | Takılı Ekipmanlar **",
        value="\n".join(active_lines),
        inline=False,
    )

    await ctx.send(embed=embed)

# 7) Admin Bakiye Ekle Komutu
@bot.command(aliases=["bakıyeekle", "paraekle"])
async def bakiyeekle(ctx, member: discord.Member, miktar: int):
    has_role = any(role.id == OWNER_ROLE_ID for role in ctx.author.roles)
    if not has_role:
        await ctx.send(
            "** ❌ | Bu Komutu Kullanmak İçin Gerekli Yetkiye Sahip Değilsiniz. **"
        )
        return

    user_balances[member.id] += miktar
    yeni_bakiye = user_balances[member.id]
    await ctx.send(
        f"** ✅ | Başarılı Bir Şekilde {member.mention} Kullanıcısına {miktar} Bakiye Eklendi. Yeni Bakiyesi: {yeni_bakiye} **"
    )

# 8) Admin Bakiye Sil Komutu
@bot.command(aliases=["bakıyesil", "parasil"])
async def bakiyesil(ctx, member: discord.Member, miktar: int):
    has_role = any(role.id == OWNER_ROLE_ID for role in ctx.author.roles)
    if not has_role:
        await ctx.send(
            "** ❌ | Bu Komutu Kullanmak İçin Gerekli Yetkiye Sahip Değilsiniz. **"
        )
        return

    user_balances[member.id] -= miktar
    yeni_bakiye = user_balances[member.id]
    await ctx.send(
        f"** ✅ | Başarılı Bir Şekilde {member.mention} Kullanıcısından {miktar} Bakiye Silinmiştir. Yeni Bakiyesi: {yeni_bakiye} **"
    )

# 9) Mağaza Komutu
@bot.command(aliases=["mağaza", "shop", "store"])
async def magaza(ctx):
    embed = discord.Embed(
        title="** 🛒 | Balıkçılık Mağazası **", color=discord.Color.green()
    )
    embed.add_field(
        name="** 🎣 | Süper Olta **",
        value="** Fiyat: ** **100000** Bakiye\n** Satın Al: ** **`a!al super_olta`**",
        inline=False,
    )
    embed.add_field(
        name="** 🪱 | Altın Yem **",
        value="** Fiyat: ** **5000** Bakiye\n** Satın Al: ** **`a!al altin_yem`**",
        inline=False,
    )
    await ctx.send(embed=embed)

# 10) Satın Al Komutu
@bot.command(aliases=["buy", "satınal", "satinal"])
async def al(ctx, *, esya: str):
    user_id = ctx.author.id
    bal = user_balances[user_id]
    esya = esya.lower().strip()

    if esya in ["super_olta", "süper olta", "superolta"]:
        if bal < 100000:
            await ctx.send(
                "** ❌ | Süper Olta Satın Almak İçin 100000 Bakiyeniz Olması Gerekmektedir. **"
            )
            return
        user_balances[user_id] -= 100000
        user_inventories[user_id]["super_olta"] += 1
        await ctx.send(
            "** ✅ | Süper Olta Başarılı Bir Şekilde Satın Alındı. a!oltakullan Yazarak Kuşanabilirsiniz. **"
        )

    elif esya in ["altin_yem", "altın yem", "altinyem"]:
        if bal < 5000:
            await ctx.send(
                "** ❌ | Altın Yem Satın Almak İçin 5000 Bakiyeniz Olması Gerekmektedir. **"
            )
            return
        user_balances[user_id] -= 5000
        user_inventories[user_id]["altin_yem"] += 1
        await ctx.send(
            "** ✅ | Altın Yem Başarılı Bir Şekilde Satın Alındı. a!yemkullan Yazarak Kuşanabilirsiniz. **"
        )
    else:
        await ctx.send(
            "** ❌ | Geçersiz Eşya Adı. Kullanım: `a!al super_olta` Veya `a!al altin_yem` **"
        )

# 11) Ekipman Kullanım Komutları
@bot.command(aliases=["oltakullanım", "oltatak"])
async def oltakullan(ctx):
    user_id = ctx.author.id
    if user_inventories[user_id]["super_olta"] < 1:
        await ctx.send("** ❌ | Envanterinizde Süper Olta Bulunmamaktadır. **")
        return
    user_equipped[user_id]["olta"] = "Süper Olta"
    await ctx.send("** ✅ | Süper Olta Başarıyla Takıldı. **")

@bot.command(aliases=["oltacıkart", "oltacikar"])
async def oltaçıkart(ctx):
    user_id = ctx.author.id
    if not user_equipped[user_id]["olta"]:
        await ctx.send("** ❌ | Takılı Bir Oltanız Bulunmamaktadır. **")
        return
    user_equipped[user_id]["olta"] = None
    await ctx.send("** ✅ | Olta Başarıyla Çıkartıldı. **")

@bot.command(aliases=["yemkullanım", "yemtak"])
async def yemkullan(ctx):
    user_id = ctx.author.id
    if user_inventories[user_id]["altin_yem"] < 1:
        await ctx.send("** ❌ | Envanterinizde Altın Yem Bulunmamaktadır. **")
        return
    user_equipped[user_id]["yem"] = "Altın Yem"
    await ctx.send("** ✅ | Altın Yem Başarıyla Takıldı. **")

@bot.command(aliases=["yemcıkart", "yemcikar"])
async def yemçıkart(ctx):
    user_id = ctx.author.id
    if not user_equipped[user_id]["yem"]:
        await ctx.send("** ❌ | Takılı Bir Yeminiz Bulunmamaktadır. **")
        return
    user_equipped[user_id]["yem"] = None
    await ctx.send("** ✅ | Yem Başarıyla Çıkartıldı. **")

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
        value="`a!bakiye` `a!magaza` `a!al`",
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

# 12) Yardım Komutu
@bot.command(aliases=["yardim", "help"])
async def yardım(ctx):
    await ctx.send(embed=get_help_embed())

# 13) Slash Yardım Komutu
@bot.tree.command(name="yardım", description="Bot Komut Menüsünü Gösterir.")
async def slash_yardim(interaction: discord.Interaction):
    await interaction.response.send_message(embed=get_help_embed())

token = os.getenv("BOT_TOKEN")
bot.run(token)
