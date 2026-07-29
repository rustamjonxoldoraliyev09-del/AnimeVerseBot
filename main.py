import os
import time
import sqlite3
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# ----------------- SIZNING SOZLAMALARINGIZ -----------------
TOKEN = "8806794822:AAGKlVLI0NrjePyzCBNIfvag1Gz5WsRO-fk"
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
    row_buttons = []
    num_episodes = int(total_episodes)
    for i in range(1, num_episodes + 1):
        row_buttons.append(types.InlineKeyboardButton(text=str(i), callback_data=f"ep_{anime_code}_{i}"))
        if len(row_buttons) == 5:
            markup.row(*row_buttons)
            row_buttons = []
    if row_buttons:
        markup.row(*row_buttons)
    return markup

def check_sub(user_id):
    try:
        member = bot.get_chat_member(KANAL_ID, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception:
        return False

# ----------------- BOT BUYRUQLARI -----------------

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    start_text = (
        "Assalomu alaykum bizning botimizga xush kelibsiz!!!\n"
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
    text_content = message.text.replace("/addanime", "").strip()
    anime_id = "101"
    if text_content:
        anime_id = text_content
    
    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, photo, episodes_count, country, language, year, genre, views, channel_link FROM animes WHERE code=?", (anime_id,))
    anime = cursor.fetchone()
    conn.close()
    
    if anime:
        title, photo, ep_count, country, lang, year, genre, views, ch_link = anime
        bot_info = bot.get_me()
        channel_caption = (
            f"🎬 <b>Nomi:</b> {title}\n\n"
            f"🥷 <b>Qismi:</b> {ep_count}\n"
            f"🌍 <b>Davlati:</b> {country}\n"
            f"🎞 <b>Tili:</b> {lang}\n"
            f"📅 <b>Yili:</b> {year}\n"
            f"🎭 <b>Janri:</b> {genre}\n\n"
            f"🔍 <b>Qidirishlar soni:</b> {views}\n\n"
            f"🍿 {ch_link}"
        )
        channel_markup = types.InlineKeyboardMarkup()
        bot_link = f"https://t.me{bot_info.username}?start=anime{anime_id}"
        btn_go_bot = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", url=bot_link)
        channel_markup.add(btn_go_bot)
        bot.send_photo(chat_id=KANAL_ID, photo=photo, caption=channel_caption, parse_mode="HTML", reply_markup=channel_markup)
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
        if len(parts) < 10:
            bot.reply_to(message, "❌ Xato! Format: kod|nomi|rasm_linki|qismlar|davlat|til|yil|janr|ko'rishlar|kanal_link")
            return
            
        a_code, a_title, a_photo, a_ep_raw, a_country, a_lang, a_year, a_genre, a_views, a_link = parts[:10]
        
        conn = sqlite3.connect("anime_bot.db")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO animes (code, title, photo, episodes_count, country, language, year, genre, views, channel_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
        (a_code.strip(), a_title.strip(), a_photo.strip(), int(a_ep_raw.strip()), a_country.strip(), a_lang.strip(), a_year.strip(), a_genre.strip(), a_views.strip(), a_link.strip()))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ {a_title.strip()} bazaga qo'shildi!")
    except Exception as e:
        bot.reply_to(message, f"❌ Xato! Formatni tekshiring. (Xatolik: {e})")

@bot.message_handler(commands=['addep'])
def admin_add_episode(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.reply_to_message or not message.reply_to_message.video:
        bot.reply_to(message, "⚠️ Xato: Avval videoga reply qilib buyruq yozing!")
        return
    try:
        args_text = message.text.replace("/addep ", "").strip()
        args = args_text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Xato! Format: `/addep 101 1`")
            return
            
        anime_code, ep_num_raw = args[:2]
        ep_num = int(ep_num_raw)
        video_id = message.reply_to_message.video.file_id
        
        conn = sqlite3.connect("anime_bot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO episodes (anime_code, episode_number, video_id) VALUES (?, ?, ?)", (anime_code, ep_num, video_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Kod {anime_code}: {ep_num}-qism saqlandi!")
    except Exception as e:
        bot.reply_to(message, f"❌ Xato! (Xatolik: {e})")

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
    cursor.execute("SELECT title, photo, episodes_count, country, language, year, genre, views, channel_link FROM animes WHERE code=?", (code,))
    anime = cursor.fetchone()
    conn.close()
    
    if anime:
        title, photo, ep_count, country, lang, year, genre, views, ch_link = anime
        caption = (
            f"🎬 <b>Nomi:</b> {title}\n\n"
            f"🥷 <b>Qismi:</b> {ep_count}\n"
            f"🌍 <b>Davlati:</b> {country}\n"
            f"🎞 <b>Tili:</b> {lang}\n"
            f"📅 <b>Yili:</b> {year}\n"
            f"🎭 <b>Janri:</b> {genre}\n\n"
            f"🔍 <b>Qidirishlar soni:</b> {views}\n\n"
            f"🍿 {ch_link}"
        )
        markup = get_episodes_grid(code, int(ep_count))
        bot.send_photo(chat_id=user_id, photo=photo, caption=caption, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(user_id, "❌ Bunday kodli anime topilmadi.")

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
            video_file_id, = row
            bot.send_video(chat_id=call.message.chat.id, video=video_file_id, caption=f"{ep_num}-qism")
        else:
            bot.answer_callback_query(call.id, "⚠️ Videosi hali yuklanmagan!", show_alert=True)
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
            print(f"Xatolik ulanishda: {e}")
            time.sleep(5)
                            
