from pymongo import MongoClient

# MONGO KODINGIZNI QO'YING VA PAROLINGIZNI YOZING!
MONGO_URL = "mongodb+srv://rustamjonxoldoraliyev09_db_user:PAROLINGIZ@clunster0.n0daf0n.mongodb.net/?appName=Clunster0"
"

client = MongoClient(MONGO_URL)
db = client["anime_verse_database"]

# Jadvallar (Kolleksiyalar)
animes_col = db["animes"]
episodes_col = db["episodes"]

def init_db():
    """ Test uchun 101 kodli animeni avtomatik bazaga qo'shish """
    anime = animes_col.find_one({"_id": "101"})
    if not anime:
        anime_data = {
            "_id": "101",
            "title": "Shilliq sifatida qayta tug'ilganim haqida (1-fasl)",
            "photo": "https://justwatch.com",
            "episodes_count": 24,
            "country": "Yaponiya",
            "language": "O'ZBEK tilida",
            "year": "2018",
            "genre": "Ekshn, Komediya, Fentezi, O'zga Dunyo",
            "views": "17366",
            "channel_link": "@an1verseuz"
        }
        animes_col.insert_one(anime_data)
        
