import os
import time
import telebot
from telebot import types
from flask import Flask
from threading import Thread
# database.py faylidan jadvallarni chaqirib olamiz
from database import animes_col, episodes_col, init_db

# ----------------- SIZNING SOZLAMALARINGIZ -----------------
TOKEN = "8806794822:AAFpEogBBbMylV1FRLZO5MdgkQ4QJtJHC_c"
KANAL_ID = "@an1verseuz"
ADMIN_ID = 8370334471

bot = telebot.TeleBot(TOKEN)
app = Flask('')

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
    anime_id = args[1] if len(args) > 1 else "101"
    anime = animes_col.find_one({"_id": anime_id})
    
    if anime:
        bot_info = bot.get_me()
        channel_caption = (
            f"🎬 **Nomi:** {anime['title']}\n\n🥷 **Qismi:** 24/{anime['episodes_count']}\n"
            f"🌍 **Davlati:** {anime['country']}\n"
            f"🎞 **Tili:** {anime['language']}\n📅 **Yili:** {anime['year']}\n"
            f"🎭 **Janri:** {anime['genre']}\n\n🔍 **Qidirishlar soni:** {anime['views']}\n\n🍿 {anime['channel_link']}"
        )
        channel_markup = types.InlineKeyboardMarkup()
        bot_link = f"https://t.me{bot_info.username}?start=anime{anime_id}"
        btn_go_bot = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", url=bot_link)
        channel_markup.add(btn_go_bot)
        bot.send_photo(chat_id=KANAL_ID, photo=anime['photo'], caption=channel_caption, parse_mode="Markdown", reply_markup=channel_markup)
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
        anime_id = parts[0].strip()
        anime_data = {
            "_id": anime_id,
            "title": parts[1].strip(),
            "photo": parts[2].strip(),
            "episodes_count": int(parts[3].strip()),
            "country": parts[4].strip(),
            "language": parts[5].strip(),
            "year": parts[6].strip(),
            "genre": parts[7].strip(),
            "views": parts[8].strip(),
            "channel_link": parts[9].strip()
        }
        animes_col.replace_one({"_id": anime_id}, anime_data, upsert=True)
        bot.reply_to(message, f"✅ {anime_data['title']} (Kod: {anime_id}) bazaga qo'shildi!")
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
        anime_code = args[0]
        ep_num = int(args[1])
        video_id = message.reply_to_message.video.file_id
        episode_data = {"anime_code": anime_code, "episode_number": ep_num, "video_id": video_id}
        episodes_col.replace_one({"anime_code": anime_code, "episode_number": ep_num}, episode_data, upsert=True)
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
    anime = animes_col.find_one({"_id": code})
    if anime:
        caption = (
            f"🎬 **Nomi:** {anime['title']}\n\n🥷 **Qismi:** 24/{anime['episodes_count']}\n"
            f"🌍 **Davlati:** {anime['country']}\n"
            f"🎞 **Tili:** {anime['language']}\n📅 **Yili:** {anime['year']}\n"
            f"🎭 **Janri:** {anime['genre']}\n\n🔍 **Qidirishlar soni:** {anime['views']}\n\n🍿 {anime['channel_link']}"
        )
        markup = get_episodes_grid(code, anime['episodes_count'])
        bot.send_photo(chat_id=user_id, photo=anime['photo'], caption=caption, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(user_id, "❌ Bunday kodli anime topilmadi. Qayta urinib ko'ring.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ep_"))
def send_episode_callback(call):
    try:
        _, anime_code, ep_num = call.data.split("_")
        row = episodes_col.find_one({"anime_code": anime_code, "episode_number": int(ep_num)})
        if row:
            bot.send_video(chat_id=call.message.chat.id, video=row['video_id'], caption=f"{ep_num}-qism")
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
      
