import os
import time
import sqlite3
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# ----------------- SIZNING SOZLAMALARINGIZ -----------------
TOKEN = "8806794822:AAFhUWB2jUEQ3vi16G5R6YW0PwTNVzapFh4"
KANAL_ID = "@an1verseuz"
ADMIN_ID = 8370334471

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# ----------------- MA'LUMOTLAR OMBORI (SQLITE) -----------------
def init_db():
    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS animes (
        code TEXT PRIMARY KEY,
        title TEXT,
        photo TEXT,
        episodes_count INTEGER,
        country TEXT,
        language TEXT,
        year TEXT,
        genre TEXT,
        views TEXT,
        channel_link TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_code TEXT,
        episode_number INTEGER,
        video_id TEXT
    )""")
    cursor.execute("SELECT code FROM animes WHERE code='101'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO animes VALUES (
            '101', "Shilliq sifatida qayta tug'ilganim haqida (1-fasl)", 
            'https://justwatch.com', 
            24, 'Yaponiya', "O'ZBEK tilida", '2018', "Ekshn, Komediya, Fentezi, O'zga Dunyo", '17366', '@an1verseuz'
        )""")
    conn.commit()
    conn.close()

def get_episodes_grid(anime_code, total_episodes):
    markup = types.InlineKeyboardMarkup()
    row = []
    for i in range(1, total_episodes + 1):
        row.append(types.InlineKeyboardButton(text=str(i), callback_data=f"ep_{anime_code}_{i}"))
        if len(row) == 5:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    return markup

def check_sub(user_id):
    try:
        member = bot.get_chat_member(KANAL_ID, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception:
        return False
    @bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    start_text = (
        "Assalomu alaykum bizning botimizga xush kelibsiz!!! "
        "Tomosha qilish uchun Kodni... yozing... ✔️\n\n"
        "Murojat va takliflar uchun:\n\n@An1verseuzb✔️\n\n"
        "Botdan to'liq foydalanish uchun homiy kanalga azo bo'ling!! ✔️"
    )
    bot.send_message(user_id, start_text)
    
    if check_sub(user_id):
        show_search_menu(user_id)
    else:
        markup = types.InlineKeyboardMarkup()
        username_clean = KANAL_ID.replace('@', '')
        markup.add(types.InlineKeyboardButton(text="An1Verse", url=f"tg://resolve?domain={username_clean}"))
        markup.add(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
        bot.send_message(user_id, "🛑 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_callback(call):
    user_id = call.from_user.id
    if check_sub(user_id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        show_search_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

def show_search_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔍 Anime qidirish"))
    bot.send_message(user_id, "Pastdagi tugmani bosib anime qidirishingiz mumkin 👇", reply_markup=markup)

@bot.message_handler(commands=['addanime'])
def admin_add_anime_to_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    anime_id = args if len(args) > 1 else "101"
    
    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes WHERE code=?", (anime_id,))
    anime = cursor.fetchone()
    conn.close()
    
    if anime:
        bot_info = bot.get_me()
        channel_caption = (
            f"🎬 **Nomi:** {anime}\n\n🥷 **Qismi:** 24/{anime}\n"
            f"🌍 **Davlati:** {anime}\n"
            f"🎞 **Tili:** {anime}\n📅 **Yili:** {anime}\n"
            f"🎭 **Janri:** {anime}\n\n🔍 **Qidirishlar soni:** {anime}\n\n🍿 {anime}"
        )
        channel_markup = types.InlineKeyboardMarkup()
        bot_link = f"https://t.me{bot_info.username}?start=anime{anime_id}"
        btn_go_bot = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", url=bot_link)
        channel_markup.add(btn_go_bot)
        bot.send_photo(chat_id=KANAL_ID, photo=anime, caption=channel_caption, parse_mode="Markdown", reply_markup=channel_markup)
        bot.reply_to(message, "✅ Post kanalingizga muvaffaqiyatli yuborildi!")
    else:
        bot.reply_to(message, f"❌ Kod {anime_id} bo'yicha anime bazada topilmadi!")

@bot.message_handler(commands=['addanime_db'])
def admin_add_anime_to_db(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        text = message.text.replace("/addanime_db ", "").strip()
        parts = text.split("|")
        anime_id = parts.strip()
        
        conn = sqlite3.connect("anime_bot.db")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO animes (code, title, photo, episodes_count, country, language, year, genre, views, channel_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
        (anime_id, parts.strip(), parts.strip(), int(parts.strip()), parts.strip(), parts.strip(), parts.strip(), parts.strip(), parts.strip(), parts.strip()))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ {parts.strip()} (Kod: {anime_id}) bazaga qo'shildi!")
    except Exception as e:
        bot.reply_to(message, f"❌ Xato! Formatni tekshiring. (Xatolik: {e})")

@bot.message_handler(commands=['addep'])
def admin_add_episode(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.reply_to_message or not message.reply_to_message.video:
        bot.reply_to(message, "⚠️ Xato: Avval videoga reply qilib, keyin buyruqni yozing!")
        return
    try:
        args = message.text.replace("/addep ", "").split()
        anime_code = args
        ep_num = int(args)
        video_id = message.reply_to_message.video.file_id
        
        conn = sqlite3.connect("anime_bot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO episodes (anime_code, episode_number, video_id) VALUES (?, ?, ?)", (anime_code, ep_num, video_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Kod {anime_code}: {ep_num}-qism bazaga saqlandi!")
    except Exception as e:
        bot.reply_to(message, f"❌ Xato! Format: `/addep 101 1` (Xatolik: {e})")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if not check_sub(user_id):
        bot.send_message(user_id, "🛑 Kanalga a'zolikdan chiqib ketgansiz! Qayta start bosing: /start")
        return
    if message.text == "🔍 Anime qidirish":
        bot.send_message(user_id, "Anime kodini kiriting (Masalan: 101):")
        return
        
    code = message.text.strip()
    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes WHERE code=?", (code,))
    anime = cursor.fetchone()
    conn.close()
    
    if anime:
        caption = (
            f"🎬 **Nomi:** {anime}\n\n🥷 **Qismi:** 24/{anime}\n"
            f"🌍 **Davlati:** {anime}\n"
            f"🎞 **Tili:** {anime}\n📅 **Yili:** {anime}\n"
            f"🎭 **Janri:** {anime}\n\n🔍 **Qidirishlar soni:** {anime}\n\n🍿 {anime}"
        )
        markup = get_episodes_grid(code, anime)
        bot.send_photo(chat_id=user_id, photo=anime, caption=caption, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(user_id, "❌ Bunday kodli anime topilmadi. Qayta urinib ko'ring.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ep_"))
def send_episode_callback(call):
    try:
        _, anime_code, ep_num = call.data.split("_")
        conn = sqlite3.connect("anime_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT video_id FROM episodes WHERE anime_code=? AND episode_number=?", (anime_code, int(ep_num)))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            bot.send_video(chat_id=call.message.chat.id, video=row, caption=f"{ep_num}-qism")
        else:
            bot.answer_callback_query(call.id, "⚠️ Bu qism videosi hali serverga yuklanmagan!", show_alert=True)
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Xatolik: {e}")

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()
    t = Thread(target=run)
    t.start()
    print("Bot muvaffaqiyatli ishga tushdi...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"Xatolik bo'ldi, 5 soniyadan keyin qayta ulanadi: {e}")
            time.sleep(5)
