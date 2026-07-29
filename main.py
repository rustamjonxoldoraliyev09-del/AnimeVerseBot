import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import pymongo

# ----------------- SOZLAMALAR -----------------
TOKEN = os.getenv("TOKEN", "8806794822:AAEqEAUPW6d_R2NPQ2R67tEUS4R1hLuRszA")
MONGO_URI = os.getenv("mongodb+srv://rustamjonxoldoraliyev09_db_user:qwertuypoi98@clunster0.n0daf0n.mongodb.net/?retryWrites=true&w=majority&appName=Clunster0") 
KANAL_ID = "@an1verseuz"
ADMIN_ID = 8370334471

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# ----------------- MONGODB ULANISH -----------------
client = None
db = None

try:
    if MONGO_URI:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['anime_bot_db']
        print("✅ MongoDB bazasiga muvaffaqiyatli ulandi!")
    else:
        print("⚠️ DIQQAT: MONGO_URI kiritilmagan! Bot bazasiz ishlamaydi.")
except Exception as e:
    print(f"❌ Bazaga ulanishda xatolik: {e}")

# ----------------- YORDAMCHI FUNKSIYALAR -----------------

def init_db():
    """Bot ishlaganda avtomatik Test Anime va 1-qismni qo'shadi"""
    if db is None: return

    # 1. Animeni tekshiramiz va qo'shamiz
    animes = db['animes']
    if animes.count_documents({'code': '101'}) == 0:
        animes.insert_one({
            'code': '101',
            'title': "Test Anime: Shilliq (Namuna)",
            'photo': 'https://assets.jalantikus.com/assets/cache/560/350/userfiles/2020/01/24/telsei-shitara-slime-datta-ken-a9163.jpg', 
            'episodes_count': 12,
            'country': 'Yaponiya',
            'language': "O'ZBEK tilida",
            'year': '2024',
            'genre': "Test, Fantastika",
            'views': 0,
            'channel_link': '@an1verseuz'
        })
        print("ℹ️ Test Anime (101) bazaga qo'shildi.")

    # 2. Shu animening 1-qismini ham qo'shamiz (Test uchun)
    episodes = db['episodes']
    if episodes.count_documents({'anime_code': '101', 'episode': 1}) == 0:
        episodes.insert_one({
            'anime_code': '101',
            'episode': 1,
            'file_id': 'https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4' # Test video link
            # Eslatma: Real botda bu yerga Telegram file_id qo'yiladi
        })
        print("ℹ️ Test Qism (1-qism) bazaga qo'shildi.")

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

# ----------------- BOT BUYRUQLARI -----------------

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    init_db() # Har start bosilganda bazani tekshirib, yo'q narsalarni tiklaydi
    
    start_text = "Assalomu alaykum! Anime ko'rish uchun kodni yozing (Masalan: 101)"
    
    if check_sub(user_id):
        bot.send_message(user_id, start_text)
        show_search_menu(user_id)
    else:
        markup = types.InlineKeyboardMarkup()
        clean_username = KANAL_ID.replace('@', '')
        markup.add(types.InlineKeyboardButton("A'zo bo'lish", url=f"https://t.me/{clean_username}"))
        markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription"))
        bot.send_message(user_id, f"Botdan foydalanish uchun {KANAL_ID} kanaliga a'zo bo'ling!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Obuna tasdiqlandi!")
        show_search_menu(call.from_user.id)
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!", show_alert=True)

# ----------------- ANIME QIDIRISH VA KO'RISH -----------------

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "🔍 Anime qidirish":
        bot.reply_to(message, "Marhamat, anime kodini yozing (Masalan: 101)")
        return

    if message.text.isdigit() and db is not None:
        code = message.text
        anime = db['animes'].find_one({'code': code})
        
        if anime:
            caption = (
                f"🎬 <b>{anime.get('title')}</b>\n"
                f"🌍 Davlat: {anime.get('country')}\n"
                f"🇺🇿 Til: {anime.get('language')}\n"
                f"💿 Qismlar: {anime.get('episodes_count')}"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📥 Qismlarni ko'rish", callback_data=f"view_{code}"))
            
            try:
                if anime.get('photo') and anime.get('photo').startswith('http'):
                    bot.send_photo(message.chat.id, anime['photo'], caption=caption, parse_mode='HTML', reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, caption, parse_mode='HTML', reply_markup=markup)
            except:
                bot.send_message(message.chat.id, caption, parse_mode='HTML', reply_markup=markup)
        else:
            bot.reply_to(message, "❌ Bunday kodli anime topilmadi.")

# "Qismlarni ko'rish" bosilganda ishlaydigan funksiya
@bot.callback_query_handler(func=lambda call: call.data.startswith('view_'))
def view_episodes(call):
    code = call.data.split('_')[1]
    anime = db['animes'].find_one({'code': code})
    
    if not anime:
        bot.answer_callback_query(call.id, "Anime topilmadi!")
        return

    # Tugmachalarni yaratish (1, 2, 3...)
    markup = types.InlineKeyboardMarkup()
    buttons = []
    count = int(anime.get('episodes_count', 0))
    
    for i in range(1, count + 1):
        buttons.append(types.InlineKeyboardButton(str(i), callback_data=f"ep_{code}_{i}"))
        if len(buttons) == 5: # Bir qatorda 5 ta tugma
            markup.row(*buttons)
            buttons = []
    if buttons:
        markup.row(*buttons)
        
    bot.send_message(call.message.chat.id, f"📺 <b>{anime['title']}</b>\nQismni tanlang:", parse_mode='HTML', reply_markup=markup)

# Qism (1, 2...) bosilganda videoni yuborish
@bot.callback_query_handler(func=lambda call: call.data.startswith('ep_'))
def send_episode(call):
    _, code, ep_num = call.data.split('_')
    ep_num = int(ep_num)
    
    episode = db['episodes'].find_one({'anime_code': code, 'episode': ep_num})
    
    if episode:
        file_id = episode['file_id']
        bot.send_message(call.message.chat.id, f"🎬 {ep_num}-qism yuklanmoqda...")
        
        # Agar file_id http link bo'lsa (Test uchun)
        if file_id.startswith('http'):
             bot.send_document(call.message.chat.id, file_id, caption=f"{ep_num}-qism")
        else:
             # Haqiqiy Telegram File ID bo'lsa
             bot.send_video(call.message.chat.id, file_id, caption=f"{ep_num}-qism")
    else:
        bot.answer_callback_query(call.id, "❌ Bu qism hali bazaga yuklanmagan.", show_alert=True)

# ----------------- ADMIN COMMANDS -----------------
@bot.message_handler(commands=['addep'])
def add_episode_command(message):
    # Foydalanish: /addep 101|1|FILE_ID_YOKI_LINK
    if message.from_user.id != ADMIN_ID: return
    try:
        _, code, ep, file_id = message.text.split('|')
        db['episodes'].update_one(
            {'anime_code': code.strip(), 'episode': int(ep)},
            {'$set': {'file_id': file_id.strip()}},
            upsert=True
        )
        bot.reply_to(message, f"✅ {code}-anime {ep}-qism saqlandi!")
    except:
        bot.reply_to(message, "Xato! Format: /addep 101|1|FILE_ID")

# ----------------- SERVER -----------------
@app.route('/')
def home():
    return "Bot Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
        
