import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# ----------------- SIZNING SOZLAMALARINGIZ -----------------
TOKEN = "8806794822:AAE9mE2bIiBsoNoUqYZzRIBOsFZH4EgrnMc"  
KANAL_ID = "@an1verseuz"  
ADMIN_ID = 8370334471  

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# Foydalanuvchilar bazasi fayli
USERS_FILE = "users.txt"

def add_user(user_id):
    """Foydalanuvchini bazaga qo'shish"""
    user_id = str(user_id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            f.write(user_id + "\n")
        return
    
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
        
    if user_id not in users:
        with open(USERS_FILE, "a") as f:
            f.write(user_id + "\n")

def get_users_count():
    """Jami foydalanuvchilar sonini olish"""
    if not os.path.exists(USERS_FILE):
        return 0
    with open(USERS_FILE, "r") as f:
        return len(f.read().splitlines())

# ----------------- TARTIBLANGAN ANIME MA'LUMOTLAR BAZASI -----------------
ANIME_DATABASE = {
    "1": {
        "id": "1",
        "title": "Solo Leveling (1-fasl)",
        "photo": "AgACAgIAAxkBAAIBaWpow4-c4gkDO1klnf6GmBbU8NcJAAIeIWsbri9JSw2BpRs3hVouAQADAgADeAADPQQ", 
        "episodes_count": 12,
        "country": "Yaponiya",
        "language": "O'ZBEK tilida",
        "year": "2024",
        "genre": "Ekshn, Sarguzasht, Fentezi",
        "views": "1420",
        "channel_link": "@an1verseuz",
        "episodes_links": {
            1: "BAACAgIAAxkBAAM5Zp...Solo_Leveling_1_Qism_Video_Kodi", 
            2: "BAACAgIAAxkBAAM6Zp...Solo_Leveling_2_Qism_Video_Kodi",
        }
    }
}

# Majburiy obunani tekshirish
def check_sub(user_id):
    try:
        member = bot.get_chat_member(KANAL_ID, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception:
        return False

# Start komandasi va Majburiy obuna o'rnatilishi
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    add_user(user_id) # Foydalanuvchini bazaga saqlash
    
    start_args = message.text.split()
    if len(start_args) > 1:
        param = start_args[1]
        if param.startswith("anime"):
            anime_id = param.replace("anime", "")
            if check_sub(user_id):

         show_episodes_by_id(message.chat.id, anime_id)
                return       
start_text = (
        "Assalomu alaykum bizning botimizga xush kelibsiz!!! "
        "Tomosha qilish uchun anime nomini yoki kodini yozing... ✔️\n\n"
        "Murojat va takliflar uchun:\n\n"
        "@An1verseuzb✔️\n\n"
        "Botdan to'liq foydalanish uchun homiy kanalga azo bo'ling!! ✔️"
    )
    bot.send_message(user_id, start_text)
    
    if check_sub(user_id):
        show_search_menu(user_id)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="An1Verse", url="tg://resolve?domain=an1verseuz"))
        markup.add(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
        bot.send_message(user_id, "🛑 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_callback(call):
    user_id = call.from_user.id
    if check_sub(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_search_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

def show_search_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔍 Anime qidirish"))
    bot.send_message(user_id, "Pastdagi tugmani bosib anime qidirishingiz mumkin 👇", reply_markup=markup)

# 📊 ADMIN UCHUN STATISTIKA FUNKSIYASI
@bot.message_handler(commands=['stat'])
def admin_stat(message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        bot.reply_to(message, f"📊 **Bot statistikasi:**\n\n👥 Jami a'zolar soni: `{count}` ta", parse_mode="Markdown")
# 📢 ADMIN UCHUN REKLAMA/XABAR TARQATISH FUNKSIYASI
@bot.message_handler(commands=['send'])
def admin_send_reclaim(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    if not os.path.exists(USERS_FILE):
        bot.reply_to(message, "❌ Foydalanuvchilar bazasi bo'sh!")
        return

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    if message.reply_to_message:
        msg_to_forward = message.reply_to_message
        success = 0
        bot.reply_to(message, f"⏳ {len(users)} ta foydalanuvchiga reklama tarqatilmoqda...")
        for u_id in users:
            try:
                bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=msg_to_forward.message_id)
                success += 1
            except Exception:
                pass
        bot.send_message(message.chat.id, f"✅ Reklama tarqatish yakunlandi!\n🎯 Yetkazildi: {success}/{len(users)}")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Reklama matnini ham yozing. Masalan:\n`/send Bugun yangi anime chiqadi!`", parse_mode="Markdown")
        return

    text_to_send = args[1]
    success = 0
    bot.reply_to(message, f"⏳ {len(users)} ta foydalanuvchiga matn tarqatilmoqda...")
    for u_id in users:
        try:
            bot.send_message(u_id, text_to_send)
            success += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ Matn muvaffaqiyatli yuborildi!\n🎯 Yetkazildi: {success}/{len(users)}")

# Admin panel uchun /list komandasi
@bot.message_handler(commands=['list'])
def admin_anime_list(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not ANIME_DATABASE:
        bot.reply_to(message, "📭 Hozircha bazada hech qanday anime yo'q.")
        return
    list_text = "📋 **Bazada bor animelar va ularning kodlari:**\n\n"
    for code, anime in ANIME_DATABASE.items():
        list_text += f"🔑 **Kod:** `{code}` — 🎬 {anime['title']} ({anime['episodes_count']} qism)\n"
    bot.send_message(message.chat.id, list_text, parse_mode="Markdown")

# Admin tomonidan kanalga post yuborish
@bot.message_handler(commands=['addanime'])
def admin_add_anime_to_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()

    if len(args) < 2:
        bot.reply_to(message, "⚠️ Iltimos, anime kodini ham kiriting. Masalan: `/addanime 1`")
        return
    anime_id = args[1]
    if anime_id in ANIME_DATABASE:
        anime = ANIME_DATABASE[anime_id]
        bot_info = bot.get_me()
        channel_caption = (
            f"🎬 **Nomi:** {anime['title']}\n\n"
            f"🥷 **Qismi:** 0/{anime['episodes_count']}\n"
            f"🌍 **Davlati:** {anime['country']}\n"
            f"🎞 **Tili:** {anime['language']}\n"
            f"📅 **Yili:** {anime['year']}\n"
            f"🎭 **Janri:** {anime['genre']}\n\n"
            f"🔍 **Qidirishlar soni:** {anime['views']}\n\n"
            f"🍿 {anime['channel_link']}"
        )
        channel_markup = types.InlineKeyboardMarkup()
        btn_go_bot = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", url=f"tg://resolve?domain={bot_info.username}&start=anime{anime_id}")
        channel_markup.add(btn_go_bot)
        bot.send_photo(chat_id=KANAL_ID, photo=anime["photo"], caption=channel_caption, parse_mode="Markdown", reply_markup=channel_markup)
        bot.reply_to(message, f"✅ Kanalga yuborildi!")

# ADMIN RASM YUBORGANIDA FILE_ID ANIQLASH
@bot.message_handler(content_types=['photo'])
def handle_admin_photo(message):
    if message.from_user.id == ADMIN_ID:
        file_id = message.photo[-1].file_id
        bot.reply_to(message, f"📸 **Rasm File ID:**\n`{file_id}`", parse_mode="Markdown")

# ADMIN VIDEO YUBORGANIDA FILE_ID ANIQLASH
@bot.message_handler(content_types=['video'])
def handle_admin_video(message):
    if message.from_user.id == ADMIN_ID:
        video_id = message.video.file_id
        response_text = (
            "🎬 **Video File ID muvaffaqiyatli aniqlandi!**\n\n"
            f"Kod:\n`{video_id}`\n\n"
            "📌 Buni nusxalab, anime qismlari (`episodes_links`) ichiga yozib qo'ying."
        )
        bot.reply_to(message, response_text, parse_mode="Markdown")
        # Anime kartasini chiroyli chiqarish uchun yordamchi funksiya
def send_anime_card(user_id, anime):
    anime_caption = (
        f"🎬 **Nomi:** {anime['title']}\n\n"
        f"🥷 **Qismi:** 0/{anime['episodes_count']}\n"
        f"🌍 **Davlati:** {anime['country']}\n"
        f"🎞 **Tili:** {anime['language']}\n"
        f"📅 **Yili:** {anime['year']}\n"
        f"🎭 **Janri:** {anime['genre']}\n\n"
        f"🔍 **Qidirishlar soni:** {anime['views']}\n\n"
        f"🍿 {anime['channel_link']}"
    )
    inline_markup = types.InlineKeyboardMarkup()
    btn_download = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", callback_data=f"open_episodes_{anime['id']}")
    inline_markup.add(btn_download)
    try:
        bot.send_photo(user_id, photo=anime["photo"], caption=anime_caption, parse_mode="Markdown", reply_markup=inline_markup)
    except Exception:
        bot.send_message(user_id, anime_caption, parse_mode="Markdown", reply_markup=inline_markup)

# Qidiruv xabarlarini va shunchaki kod yuborilgandagi holatni qayta ishlash
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    add_user(user_id)
    
    if not check_sub(user_id):
        bot.send_message(user_id, "🛑 Kanalga a'zolikdan chiqib ketgansiz! Qayta start bosing: /start")
        return
        
    if message.text == "🔍 Anime qidirish":
        
        msg = bot.send_message(user_id, "⌨️ Qidirayotgan animeyingizning **kodini** yoki **nomini** kiriting:")
        bot.register_next_step_handler(msg, process_anime_search)
        return
            # 🔥 SHUNCHAKI KOD YOKI NOM YOZILSA ISHLAYDIGAN QISM
    search_query = message.text.strip().lower()
    found_anime = None
    for key, anime in ANIME_DATABASE.items():
        if search_query == anime["id"] or search_query in anime["title"].lower():
            found_anime = anime
            break
            
    if found_anime:
        send_anime_card(user_id, found_anime)
    else:
        bot.send_message(user_id, "❌ Bunday anime topilmadi. Kod yoki nomni qayta tekshiring.")

def process_anime_search(message):
    user_id = message.from_user.id
    search_query = message.text.strip().lower()
    found_anime = None
    for key, anime in ANIME_DATABASE.items():
        if search_query == anime["id"] or search_query in anime["title"].lower():
            found_anime = anime
            break
    if found_anime:
        send_anime_card(user_id, found_anime)
    else:
        bot.send_message(user_id, "❌ Bunday anime topilmadi.")

def show_episodes_by_id(chat_id, anime_id):
    if anime_id in ANIME_DATABASE:
        anime = ANIME_DATABASE[anime_id]
        markup = types.InlineKeyboardMarkup(row_width=5)
        buttons = []
        for i in range(1, anime["episodes_count"] + 1):
            btn = types.InlineKeyboardButton(text=str(i), callback_data=f"get_ep_{anime_id}_{i}")
            buttons.append(btn)
        markup.add(*buttons)
        bot.send_message(chat_id, f"🎬 **{anime['title']}** - Qismlarni tanlang:", reply_markup=markup, parse_mode="Markdown")
        @bot.callback_query_handler(func=lambda call: call.data.startswith("open_episodes_"))
def callback_open_episodes(call):
    anime_id = call.data.replace("open_episodes_", "")
    show_episodes_by_id(call.message.chat.id, anime_id)

# FOYDALANUVCHIGA VIDEONI TO'G'RIDAN-TO'G'RI FAYL SHAKLIDA YUBORISH QISMI
@bot.callback_query_handler(func=lambda call: call.data.startswith("get_ep_"))
def callback_get_episode(call):
    data_parts = call.data.split("_")
    anime_id = data_parts[2]
    ep_num = int(data_parts[3])
    
    if anime_id in ANIME_DATABASE:
        anime = ANIME_DATABASE[anime_id]
        if ep_num in anime["episodes_links"]:
            video_file_id = anime["episodes_links"][ep_num]
            
            if video_file_id.startswith("http"):
                bot.send_message(call.message.chat.id, f"🍿 **{anime['title']}** — {ep_num}-qism havolasi:\n🔗 {video_file_id}")
            else:
                try:
                    bot.send_chat_action(call.message.chat.id, 'upload_video')
                    bot.send_video(
                        chat_id=call.message.chat.id, 
                        video=video_file_id, 
                        caption=f"🍿 **{anime['title']}** — {ep_num}-qism\n\n🤖 @{bot.get_me().username} boti orqali yuklab olindi."
                    )
                except Exception as e:
                    bot.answer_callback_query(call.id, "❌ Telegram orqali videoni yuklashda xatolik yuz berdi.", show_alert=True)
                    print(f"Video yuborish xatoligi: {e}")
        else:
            bot.answer_callback_query(call.id, "❌ Bu qism hali yuklanmagan!", show_alert=True)

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
