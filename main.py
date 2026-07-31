import os
import sqlite3
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# ----------------- SIZNING SOZLAMALARINGIZ -----------------
TOKEN = "8806794822:AAGKlVLI0NrjePyzCBNIfvag1Gz5WsRO-fk"  # Bot tokeningiz
KANAL_ID = "@an1verseuz"  # Majburiy obuna kanali
ADMIN_ID = 8370334471  # Admin ID raqamingiz

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# ----------------- MA'LUMOTLAR OMBORI (DATABASE) -----------------
def get_db_connection():
    return sqlite3.connect("anime_bot.db", check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS animes (
        code TEXT PRIMARY KEY,
        title TEXT,
        photo TEXT,
        episodes_count TEXT,
        country TEXT,
        language TEXT,
        year TEXT,
        genre TEXT,
        views TEXT,
        channel_link TEXT,
        description TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_code TEXT,
        episode_number INTEGER,
        video_id TEXT
    )""")
    conn.commit()
    conn.close()

# ----------------- INLINE TUGMALAR GENERATORI -----------------
def get_episodes_grid(anime_code, total_episodes):
    markup = types.InlineKeyboardMarkup()
    row = []
    try:
        total = int(total_episodes)
    except:
        total = 12
        
    for i in range(1, total + 1):
        row.append(types.InlineKeyboardButton(text=str(i), callback_data=f"ep_{anime_code}_{i}"))
        if len(row) == 5:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    return markup

# Majburiy obunani tekshirish
def check_sub(user_id):
    try:
        member = bot.get_chat_member(KANAL_ID, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception:
        return False

def show_search_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔍 Anime qidirish"))
    bot.send_message(user_id, "Pastdagi tugmani bosib anime qidirishingiz mumkin 👇", reply_markup=markup)

# Start komandasi (Deep-linking integratsiyasi bilan)
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    
    anime_code_from_link = None
    if len(text_args) > 1 and text_args[1].startswith("anime"):
        anime_code_from_link = text_args[1].replace("anime", "")

    if check_sub(user_id):
        if anime_code_from_link:
            send_anime_by_code(user_id, anime_code_from_link)
        else:
            start_text = (
                "Assalomu alaykum bizning botimizga xush kelibsiz!!!\n"
                "Tomosha qilish uchun Kodni yozing... ✔️\n\n"
                "Murojaat va takliflar uchun: @An1verseuzb ✔️"
            )
            bot.send_message(user_id, start_text)
            show_search_menu(user_id)
    else:
        markup = types.InlineKeyboardMarkup()
        clean_channel = KANAL_ID.replace('@', '')
        markup.add(types.InlineKeyboardButton(text="An1Verse", url=f"tg://resolve?domain={clean_channel}"))
        
        callback_data = "check_subscription"
        if anime_code_from_link:
            callback_data = f"check_sub_{anime_code_from_link}"
            
        markup.add(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data=callback_data))
        
        start_text = (
            "Assalomu alaykum bizning botimizga xush kelibsiz!!!\n"
            "Botdan to'liq foydalanish uchun homiy kanalga a'zo bo'ling!! ✔️"
        )
        bot.send_message(user_id, start_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_callback(call):
    user_id = call.from_user.id
    if check_sub(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_search_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_sub_"))
def check_callback_with_anime(call):
    user_id = call.from_user.id
    anime_code = call.data.replace("check_sub_", "")
    if check_sub(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_search_menu(user_id)
        send_anime_by_code(user_id, anime_code)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
# Animeni kod bo'yicha chiqarish funksiyasi
def send_anime_by_code(user_id, code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes WHERE code=?", (code,))
    anime = cursor.fetchone()
    conn.close()
    
    if anime:
        caption = (
            f"🎬 <b>Nomi:</b> {anime[1]}\n\n"
            f"🥷 <b>Fasl/Qism:</b> {anime[3]}\n"
            f"🌍 <b>Davlati:</b> {anime[4]}\n"
            f"🎞 <b>Tili:</b> {anime[5]}\n"
            f"📅 <b>Yili:</b> {anime[6]}\n"
            f"🎭 <b>Janri:</b> {anime[7]}\n"
            f"🔍 <b>Ko'rishlar:</b> {anime[8]}\n\n"
            f"🍿 <b>Kanalimiz:</b> {anime[9]}"
        )
        markup = get_episodes_grid(code, anime[3])
        try:
            bot.send_photo(chat_id=user_id, photo=anime[2], caption=caption, parse_mode="HTML", reply_markup=markup)
        except Exception:
            bot.send_message(chat_id=user_id, text=caption, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(user_id, "❌ Bunday kodli anime topilmadi. Qayta urinib ko'ring.")

# ----------------- RASMDAGIDEK STRUKTURADA ISHLAYDIGAN BUYRUQ -----------------
@bot.message_handler(content_types=['photo'], func=lambda message: message.caption and message.caption.startswith('/addanime_db'))
def admin_add_anime_by_palka(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        raw_text = message.caption.strip()
        parts = [p.strip() for p in raw_text.split('|')]
        
        # Birinchi bo'lakdan buyruq matnini olib tashlab, faqat toza kodni ajratamiz
        first_part = parts[0].replace('/addanime_db', '').strip()
        anime_code = first_part
        
        title = parts[1]
        episodes_count = parts[2]
        country = parts[3]
        language = parts[4]
        year = parts[5]
        genre = parts[6]
        views = parts[7]
        channel_link = parts[8]
        description = parts[9] if len(parts) > 9 else ""
        
        photo_id = message.photo[-1].file_id
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO animes (code, title, photo, episodes_count, country, language, year, genre, views, channel_link, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (anime_code, title, photo_id, episodes_count, country, language, year, genre, views, channel_link, description))
        conn.commit()
        conn.close()
        
        # RASMDAGI JAVOB MATNI:
        bot.reply_to(message, f"<b><u>/addanime_db {anime_code} | {title}...</u></b>\n\n✅ {title} (Kod: {anime_code}) bazaga muvaffaqiyatli qo'shildi!", parse_mode="HTML")
        
        # Kanalga chiroyli post chiqarish
        bot_info = bot.get_me()
        channel_caption = (
            f"🎬 <b>Nomi:</b> {title}\n\n"
            f"🥷 <b>Fasl/Qism:</b> {episodes_count}\n"
            f"🌍 <b>Davlati:</b> {country}\n"
            f"🎞 <b>Tili:</b> {language}\n"
            f"📅 <b>Yili:</b> {year}\n"
            f"🎭 <b>Janri:</b> {genre}\n\n"
            f"🍿 {channel_link}"
        )
        
        channel_markup = types.InlineKeyboardMarkup()
        btn_go_bot = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", url=f"https://t.me{bot_info.username}?start=anime{anime_code}")
        channel_markup.add(btn_go_bot)
        
        bot.send_photo(chat_id=KANAL_ID, photo=photo_id, caption=channel_caption, parse_mode="HTML", reply_markup=channel_markup)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {e}\n\nIltimos, palka belgilari ketma-ketligi to'g'ri ekanligini tekshiring!")

# Admin qismlarni qo'shishi (/addep)
@bot.message_handler(commands=['addep'])
def admin_add_episode(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.reply_to_message or not message.reply_to_message.video:
        bot.reply_to(message, "⚠️ Xato: Avval videoga reply qilib, keyin buyruqni yozing!")
        return
    try:
        args = message.text.replace("/addep ", "").split()
        anime_code = args[0]
        ep_num = int(args[1])
        video_id = message.reply_to_message.video.file_id
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO episodes (anime_code, episode_number, video_id) VALUES (?, ?, ?)", (anime_code, ep_num, video_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Kod {anime_code}: {ep_num}-qism bazaga saqlandi!")
    except Exception as e:
        bot.reply_to(message, f"❌ Xato! Format: `/addep 2 1` (Xatolik: {e})")

# Xabarlarni qabul qilish va qidiruv
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if not check_sub(user_id):
        bot.send_message(user_id, "🛑 Kanalga a'zolikdan chiqib ketgansiz! Qayta start bosing: /start")
        return

    if message.text == "🔍 Anime qidirish":
        bot.send_message(user_id, "Anime kodini kiriting (Masalan: 2):")
        return
        
    code = message.text.strip()
    send_anime_by_code(user_id, code)

# Tugma bosilganda videoni yuborish
@bot.callback_query_handler(func=lambda call: call.data.startswith("ep_"))
def send_episode_callback(call):
    _, anime_code, ep_num = call.data.split("_")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT video_id FROM episodes WHERE anime_code=? AND episode_number=?", (anime_code, int(ep_num)))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        bot.send_video(chat_id=call.message.chat.id, video=row[0], caption=f"{ep_num}-qism")
    else:
        bot.answer_callback_query(call.id, "⚠️ Bu qism videosi hali serverga yuklanmagan!", show_alert=True)
    bot.answer_callback_query(call.id)

# ----------------- FLASK & RUN -----------------
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
    bot.infinity_polling()
      
