import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# ----------------- SIZNING SOZLAMALARINGIZ -----------------
TOKEN = "8806794822:AAGKlVLI0NrjePyzCBNIfvag1Gz5WsRO-fk"  # @BotFather bergan tokenni faqat shu yerga yozing!
KANAL_ID = "@an1verseuz"  # Sizning kanalingiz
ADMIN_ID = 8370334471  # Sizning shaxsiy Telegram ID raqamingiz

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# ----------------- ANIME MA'LUMOTLAR BAZASI -----------------
ANIME_DATABASE = {
    "101": {
        "id": "101",
        "title": "Shilliq sifatida qayta tug'ilganim haqida (1-fasl)",
        # MUAMMONI HAL QILISH UCHUN BUYERGA TELEGRAM RASM LINKINI QO'YDIK:
        "photo": "https://telegra.ph", 
        "episodes_count": 24,
        "country": "Yaponiya",
        "language": "Uzbek tilida",
        "year": "2018",
        "genre": "Ekshn, Komediya, Fentezi, O'zga Dunyo",
        "views": "17366",
        "channel_link": "@an1verseuz",
        "episodes_links": {
            1: "https://t.me", 
            2: "https://t.me",
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
    
    start_args = message.text.split()
    if len(start_args) > 1 and start_args[1].startswith("anime"):
        anime_id = start_args[1].replace("anime", "")
        if check_sub(user_id):
            show_episodes_by_id(message.chat.id, anime_id)
            return
            
    start_text = (
        "Assalomu alaykum bizning botimizga xush kelibsiz!!! "
        "Tomosha qilish uchun Kodni... yozing... ✔️\n\n"
        "Murojat va takliflar uchun:\n\n"
        "@an1verseuzb✔️\n\n"
        "Botdan to'liq foydalanish uchun homiy kanalga azo bo'ling!! ✔️"
    )
    bot.send_message(user_id, start_text)
    
    if check_sub(user_id):
        show_search_menu(user_id)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="O'zga dunyo animelar | Isekai", url=f"https://t.me{KANAL_ID.replace('@', '')}"))
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

# Admin tomonidan kanalga chiroyli post yuborish (/addanime)
@bot.message_handler(commands=['addanime'])
def admin_add_anime_to_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    anime_id = "101" 
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
        btn_go_bot = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", url=f"https://t.me{bot_info.username}?start=anime{anime_id}")
        channel_markup.add(btn_go_bot)
        
        bot.send_photo(chat_id=KANAL_ID, photo=anime["photo"], caption=channel_caption, parse_mode="Markdown", reply_markup=channel_markup)
        bot.reply_to(message, "✅ Post kanalingizga muvaffaqiyatli yuborildi!")

# Qidiruv tizimi
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if not check_sub(user_id):
        bot.send_message(user_id, "🛑 Kanalga a'zolikdan chiqib ketgansiz! Qayta start bosing: /start")
        return

    if message.text == "🔍 Anime qidirish":
        msg = bot.send_message(user_id, "⌨️ Qidirayotgan animeyingizning **kodini** yoki **nomini** kiriting:")
        bot.register_next_step_handler(msg, process_anime_search)

def process_anime_search(message):
    user_id = message.from_user.id
    search_query = message.text.strip().lower()
    found_anime = None
    
    for key, anime in ANIME_DATABASE.items():
        if search_query == anime["id"] or search_query in anime["title"].lower():
            found_anime = anime
            break
            
    if found_anime:
        anime_caption = (
            f"🎬 **Nomi:** {found_anime['title']}\n\n"
            f"🥷 **Qismi:** 0/{found_anime['episodes_count']}\n"
            f"🌍 **Davlati:** {found_anime['country']}\n"
            f"🎞 **Tili:** {found_anime['language']}\n"
            f"📅 **Yili:** {found_anime['year']}\n"
            f"🎭 **Janri:** {found_anime['genre']}\n\n"
            f"🔍 **Qidirishlar soni:** {found_anime['views']}\n\n"
            f"🍿 {found_anime['channel_link']}"
        )
        inline_markup = types.InlineKeyboardMarkup()
        btn_download = types.InlineKeyboardButton(text="YUKLAB OLISH 📥", callback_data=f"open_episodes_{found_anime['id']}")
        inline_markup.add(btn_download)
        
        bot.send_photo(user_id, photo=found_anime["photo"], caption=anime_caption, parse_mode="Markdown", reply_markup=inline_markup)
    else:
        bot.send_message(user_id, "❌ Bunday anime topilmadi.")

# Dinamik qismlar tugmalari paneli
def show_episodes_by_id(chat_id, anime_id):
    if anime_id in ANIME_DATABASE:
        anime = ANIME_DATABASE[anime_id]
        markup = types.InlineKeyboardMarkup(row_width=5)
        buttons = []
        for i in range(1, anime["episodes_count"] + 1):
            btn = types.InlineKeyboardButton(text=str(i), callback_data=f"get_ep_{anime_id}_{i}")
            buttons.append(btn)
        markup.add(*buttons)
        
        nav_buttons = [
            types.InlineKeyboardButton(text="⬅️", callback_data="prev_page"),
            types.InlineKeyboardButton(text="❌", callback_data="close_panel"),
            types.InlineKeyboardButton(text="➡️", callback_data="next_page")
        ]
        markup.row(*nav_buttons)
        
        bot.send_message(chat_id=chat_id, text=f"🎬 **{anime['title']}**\n\n🔽 Yuklab olmoqchi bo'lgan qism raqamini tanlang:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("open_episodes_"))
def open_episodes_callback(call):
    anime_id = call.data.replace("open_episodes_", "")
    show_episodes_by_id(call.message.chat.id, anime_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("get_ep_"))
def get_episode_file(call):
    data_parts = call.data.split("_")
    anime_id = data_parts[2]
    ep_num = int(data_parts[3])
    
    if anime_id in ANIME_DATABASE:
        anime = ANIME_DATABASE[anime_id]
        if ep_num in anime["episodes_links"]:
            file_link = anime["episodes_links"][ep_num]
            bot.send_message(chat_id=call.message.chat.id, text=f"🎬 **{anime['title']}**\n🍿 **{ep_num}-qism**\n\n📥 Yuklab olish/Ko'rish uchun havola:\n{file_link}", parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, f"❌ Kechirasiz, {ep_num}-qism hali yuklanmagan!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "close_panel")
def close_panel_callback(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

# ----------------- RENDER SERVERDA UMRBOD YOQIB QO'YISH QISMI -----------------
@app.route('/')
def home():
    return "Bot faol ishlamoqda!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    print("Bot serverda muvaffaqiyatli yurdi!")
    bot.infinity_polling()
