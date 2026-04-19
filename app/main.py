import logging
import sqlite3
import asyncio
import sys  # <-- Bu qatorni qo'shing
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
from os import getenv
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_ID = getenv("ADMIN_ID")
logging.info("Standart sozlamalar bilan ishga tushdi")

# Conversation states - 32 ta qiymat kerak

(
    SEARCH_NAME, SEARCH_CODE, SEARCH_GENRE,
    ADD_ANIME_NAME, ADD_ANIME_EPISODE, ADD_ANIME_COUNTRY, ADD_ANIME_LANGUAGE, 
    ADD_ANIME_DESCRIPTION, ADD_ANIME_GENRE, ADD_ANIME_IMAGE,
    ADD_EPISODE_ANIME_ID, ADD_EPISODE_FILE,
    EDIT_ANIME_SELECT, EDIT_ANIME_FIELD, EDIT_ANIME_VALUE,
    EDIT_EPISODE_SELECT, EDIT_EPISODE_ANIME, EDIT_EPISODE_NUMBER, EDIT_EPISODE_FILE,
    PAYMENT_AMOUNT, PAYMENT_PHOTO,
    ADMIN_MESSAGE, USER_MESSAGE_ID, BROADCAST_MESSAGE, FORWARD_MESSAGE,
    ADD_CHANNEL_ID, ADD_CHANNEL_LINK,
    ANIME_CHANNEL_SETUP, START_TEXT_SETUP, HELP_TEXT_SETUP, ADS_TEXT_SETUP,
    BOT_SITUATION, DELETE_ANIME_ID
) = range(33)

class Database:
    def __init__(self, db_name='anime_bot.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                status TEXT DEFAULT 'Simple',
                balance INTEGER DEFAULT 0,
                vip_time TEXT DEFAULT '00.00.0000 00:00',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Anime table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                episode INTEGER DEFAULT 1,
                country TEXT,
                language TEXT,
                image TEXT,
                description TEXT,
                genre TEXT,
                rating REAL DEFAULT 0.0,
                status TEXT DEFAULT 'ongoing',
                views INTEGER DEFAULT 0,
                create_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Anime episodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anime_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_id INTEGER,
                episode_number INTEGER,
                file_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (anime_id) REFERENCES anime (id)
            )
        ''')
        
        # Channels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                channel_link TEXT,
                channel_type TEXT DEFAULT 'request'
            )
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                photo TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Bot settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Insert default settings
        default_settings = [
            ('situation', 'On'),
            ('share', 'false'),
            ('start_text', '❄️ Anime Botga xush kelibsiz!'),
            ('help_text', 'Yordam uchun admin bilan bogʻlaning.'),
            ('ads_text', 'Reklama matni'),
            ('anime_channel', '@KinoLiveUz')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)
        ''', default_settings)
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, first_name, last_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return dict(user) if user else None
    
    def update_user_balance(self, user_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET balance = balance + ? WHERE user_id = ?
        ''', (amount, user_id))
        
        conn.commit()
        conn.close()
    
    def set_user_vip(self, user_id, vip_time):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET status = "Premium +", vip_time = ? WHERE user_id = ?
        ''', (vip_time, user_id))
        
        conn.commit()
        conn.close()
    
    def add_anime(self, name, episode, country, language, image, description, genre):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO anime (name, episode, country, language, image, description, genre)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, episode, country, language, image, description, genre))
        
        anime_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return anime_id
    
    def update_anime(self, anime_id, field, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'UPDATE anime SET {field} = ? WHERE id = ?', (value, anime_id))
        
        conn.commit()
        conn.close()
    
    def delete_anime(self, anime_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Avval epizodlarni o'chirish
        cursor.execute('DELETE FROM anime_episodes WHERE anime_id = ?', (anime_id,))
        # Keyin animeni o'chirish
        cursor.execute('DELETE FROM anime WHERE id = ?', (anime_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_anime(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM anime ORDER BY id DESC')
        anime_list = cursor.fetchall()
        
        conn.close()
        return [dict(row) for row in anime_list]
    
    def add_episode(self, anime_id, episode_number, file_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO anime_episodes (anime_id, episode_number, file_id)
            VALUES (?, ?, ?)
        ''', (anime_id, episode_number, file_id))
        
        conn.commit()
        conn.close()
    
    def update_episode(self, episode_id, file_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE anime_episodes SET file_id = ? WHERE id = ?', (file_id, episode_id))
        
        conn.commit()
        conn.close()
    
    def delete_episode(self, episode_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM anime_episodes WHERE id = ?', (episode_id,))
        
        conn.commit()
        conn.close()
    
    def get_episode_by_id(self, episode_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM anime_episodes WHERE id = ?', (episode_id,))
        episode = cursor.fetchone()
        
        conn.close()
        return dict(episode) if episode else None
    
    def search_anime_by_name(self, name):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM anime WHERE name LIKE ? LIMIT 10
        ''', (f'%{name}%',))
        
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    def search_anime_by_id(self, anime_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM anime WHERE id = ?', (anime_id,))
        result = cursor.fetchone()
        
        conn.close()
        return dict(result) if result else None
    
    def search_anime_by_genre(self, genre):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM anime WHERE genre LIKE ? LIMIT 10
        ''', (f'%{genre}%',))
        
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    def get_anime_episodes(self, anime_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM anime_episodes WHERE anime_id = ? ORDER BY episode_number
        ''', (anime_id,))
        
        episodes = cursor.fetchall()
        conn.close()
        return [dict(row) for row in episodes]
    
    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        
        conn.close()
        return [user[0] for user in users]
    
    def get_user_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_setting(self, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def update_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)
        ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def add_channel(self, channel_id, channel_link, channel_type='request'):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO channels (channel_id, channel_link, channel_type)
            VALUES (?, ?, ?)
        ''', (channel_id, channel_link, channel_type))
        
        conn.commit()
        conn.close()
    
    def get_channels(self, channel_type='request'):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM channels WHERE channel_type = ?', (channel_type,))
        channels = cursor.fetchall()
        
        conn.close()
        return [dict(row) for row in channels]
    
    def delete_channel(self, channel_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
        
        conn.commit()
        conn.close()
    
    def add_payment(self, user_id, amount, photo):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payments (user_id, amount, photo) VALUES (?, ?, ?)
        ''', (user_id, amount, photo))
        
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return payment_id
    
    def update_payment_status(self, payment_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE payments SET status = ? WHERE id = ?', (status, payment_id))
        
        conn.commit()
        conn.close()

# Keyboard functions
def main_menu_keyboard():
    keyboard = [
        ['🔎 Anime izlash'],
        ['💎 Premium +', '👤 Hisobim'],
        ['✉️ Adminga murojaat']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def search_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🗞 Nom orqali", callback_data="search_name"),
            InlineKeyboardButton("🔢 Kod orqali", callback_data="search_code")
        ],
        [
            InlineKeyboardButton("💎 Janr orqali", callback_data="search_genre")
        ],
        [
            InlineKeyboardButton("🔙 Ortga", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    keyboard = [[InlineKeyboardButton("🔙 Ortga", callback_data="back_main")]]
    return InlineKeyboardMarkup(keyboard)

def back_admin_button():
    keyboard = [[InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")]]
    return InlineKeyboardMarkup(keyboard)

def admin_panel_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔧 Asosiy sozlamlar", callback_data="main_settings"),
            InlineKeyboardButton("🎥 Anime sozlamlari", callback_data="anime_settings")
        ],
        [
            InlineKeyboardButton("📝 Post tayyorlash", callback_data="create_post"),
            InlineKeyboardButton("📣 Kanallar", callback_data="channel_settings")
        ],
        [
            InlineKeyboardButton("📈 Statistika", callback_data="stats"),
            InlineKeyboardButton("✉️ Xabar yuborish", callback_data="send_message")
        ],
        [
            InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="user_management")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def anime_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎥 Anime qo'shish", callback_data="add_anime"),
            InlineKeyboardButton("📀 Qism qo'shish", callback_data="add_episode")
        ],
        [
            InlineKeyboardButton("✏️ Anime tahrirlash", callback_data="edit_anime"),
            InlineKeyboardButton("🎬 Qism tahrirlash", callback_data="edit_episode")
        ],
        [
            InlineKeyboardButton("🗑 Anime o'chirish", callback_data="delete_anime"),
            InlineKeyboardButton("📋 Anime ro'yxati", callback_data="list_anime")
        ],
        [
            InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def channel_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔐 Majburiy obunalar", callback_data="mandatory_subscriptions")
        ],
        [
            InlineKeyboardButton("🎥 Anime kanal", callback_data="anime_channel_setup")
        ],
        [
            InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def main_settings_keyboard(db):
    share_status = db.get_setting('share')
    share_text = "✅ Uzatish yoqish" if share_status == "false" else "❌ Uzatish o'chirish"
    
    keyboard = [
        [InlineKeyboardButton(share_text, callback_data="toggle_share")],
        [
            InlineKeyboardButton("📝 Start matni", callback_data="start_text_setup"),
            InlineKeyboardButton("🤖 Bot holati", callback_data="bot_situation_setup")
        ],
        [
            InlineKeyboardButton("ℹ️ Yordam matni", callback_data="help_text_setup"),
            InlineKeyboardButton("📢 Reklama matni", callback_data="ads_text_setup")
        ],
        [InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def mandatory_channels_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Qo'shish", callback_data="add_channel")],
        [
            InlineKeyboardButton("📃 Ro'yxat", callback_data="list_channels"),
            InlineKeyboardButton("🗑 O'chirish", callback_data="delete_channel")
        ],
        [InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def send_message_keyboard():
    keyboard = [
        [InlineKeyboardButton("👤 Userga", callback_data="user_message")],
        [InlineKeyboardButton("👥 Oddiy xabar", callback_data="broadcast_message")],
        [InlineKeyboardButton("📩 Forward xabar", callback_data="forward_message")],
        [InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def premium_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 30 kun - 5,000 UZS", callback_data="buy_premium")],
        [InlineKeyboardButton("🔙 Ortga", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def profile_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Pul kiritish", callback_data="add_money")],
        [InlineKeyboardButton("🔙 Ortga", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_confirmation_keyboard(payment_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_payment_{payment_id}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_payment_{payment_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def ask_question_keyboard():
    keyboard = [[
        InlineKeyboardButton("✉️ Yana savol berish", callback_data="ask_question")
    ]]
    return InlineKeyboardMarkup(keyboard)

def edit_anime_fields_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Nomi", callback_data="edit_field_name")],
        [InlineKeyboardButton("🎬 Epizodlar soni", callback_data="edit_field_episode")],
        [InlineKeyboardButton("🌍 Davlati", callback_data="edit_field_country")],
        [InlineKeyboardButton("🗣 Tili", callback_data="edit_field_language")],
        [InlineKeyboardButton("📖 Tavsifi", callback_data="edit_field_description")],
        [InlineKeyboardButton("🎭 Janri", callback_data="edit_field_genre")],
        [InlineKeyboardButton("🖼 Rasm", callback_data="edit_field_image")],
        [InlineKeyboardButton("🔙 Ortga", callback_data="anime_settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Initialize database
db = Database()

# Check channel subscription
async def check_subscription(user_id, context):
    channels = db.get_channels('request')
    if not channels:
        return True

    keyboard = []
    not_subscribed = False
    
    for i, channel in enumerate(channels):
        try:
            channel_id = channel['channel_id'] if channel['channel_id'].startswith('-100') else f"-100{channel['channel_id']}"
            chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            status = chat_member.status
            subscribed = status in ['creator', 'administrator', 'member']
        except Exception as e:
            print(f"Kanal tekshirishda xato: {e}")
            subscribed = False
        
        channel_title = channel['channel_link'].split('/')[-1] if channel['channel_link'] else f"Kanal {i+1}"
        button_text = f"✅ {channel_title}" if subscribed else f"❌ {channel_title}"
        
        if channel['channel_link']:
            keyboard.append([InlineKeyboardButton(button_text, url=channel['channel_link'])])
        else:
            keyboard.append([InlineKeyboardButton(button_text, callback_data="no_link")])
        
        if not subscribed:
            not_subscribed = True
    
    keyboard.append([InlineKeyboardButton("🔄 Tekshirish", callback_data="check_subscription")])
    
    if not_subscribed:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ <b>Botdan to'liq foydalanish uchun kanallarga obuna bo'ling!</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return False
    
    return True

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check bot situation
    situation = db.get_setting('situation')
    if situation == 'Off' and user.id != ADMIN_ID:
        await update.message.reply_text(
            "⚠️ <b>Bot vaqtincha ishlamayapti!</b>\n\n"
            "<i>Hozirda texnik ishlar olib borilmoqda. Iltimos, keyinroq urinib ko'ring.</i> ✅",
            parse_mode='HTML'
        )
        return
    
    # Check subscription
    if not await check_subscription(user.id, context):
        return
    
    if context.args:
        try:
            anime_id = int(context.args[0])
            anime = db.search_anime_by_id(anime_id)
            
            if anime:
                episodes = db.get_anime_episodes(anime_id)
                
                if episodes:
                    share_status = db.get_setting('share')
                    protect_content = share_status == 'true'
                    
                    for episode in episodes:
                        caption = f"🍿 *{anime['name']}* 🍿\n"
                        caption += "✨───────────────✨\n"
                        caption += f"🎥 *Qism:* {episode['episode_number']} / {anime['episode']}\n"
                        caption += "✨───────────────✨\n"
                        caption += f"🎬 *Anime ID:* {anime_id}\n"
                        caption += f"📜 *Til:* {anime['language']}"
                        
                        keyboard = [[
                            InlineKeyboardButton("Dasturchi", url="https://t.me/znxrofi")
                        ]]
                        
                        await update.message.reply_video(
                            video=episode['file_id'],
                            caption=caption,
                            parse_mode='Markdown',
                            protect_content=protect_content,
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                else:
                    await update.message.reply_text("Bu animeda qismlar topilmadi!")
            else:
                await update.message.reply_text("Bu anime topilmadi!")
        except ValueError:
            await update.message.reply_text("Noto'g'ri anime ID!")
    else:
        start_text = db.get_setting('start_text')
        await update.message.reply_text(
            start_text,
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )

# Main menu handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check bot situation
    situation = db.get_setting('situation')
    if situation == 'Off' and user_id != ADMIN_ID:
        return
    
    # Check subscription
    if not await check_subscription(user_id, context):
        return
    
    if text == "🔎 Anime izlash":
        await update.message.reply_text(
            "🔎 Animeni qanday izlaymiz?",
            reply_markup=search_keyboard()
        )
    
    elif text == "💎 Premium +":
        user = db.get_user(user_id)
        if user['status'] == 'Simple':
            await update.message.reply_text(
                "❌ Siz hali 💎 Premium + tarifiga obuna bo'lmadingiz!\n\n"
                "🔥 Premium + tarifining qulayliklari:\n"
                "✅ Majburiy kanalga obuna yo'q!\n"
                "📥 Anime yuklash va ulashish doim ochiq!\n"
                "⚡ Bot tezligi 2x marta oshadi!\n"
                "🔔 Yangi anime qo'shilganda bildirishnoma!\n\n"
                "📅 1 oylik Premium + obunasini sotib olish:",
                reply_markup=premium_keyboard()
            )
        else:
            await update.message.reply_text(
                f"🎉 Siz allaqachon 💎 Premium + tarifiga obuna bo'lgansiz!\n\n"
                f"📅 Obunangizning tugash muddati: {user['vip_time']}\n"
                f"⛔ Obunani uzaytirish yoki bekor qilish imkoniyati mavjud emas."
            )
    
    elif text == "👤 Hisobim":
        user = db.get_user(user_id)
        await update.message.reply_text(
            f"🧑‍💻 Sizning shaxsiy hisobingiz\n\n"
            f"💰 Balansingiz: {user['balance']} UZS\n"
            f"🆔 ID raqamingiz: <code>{user['user_id']}</code>\n"
            f"💎 Statusingiz: {user['status']}",
            reply_markup=profile_keyboard(),
            parse_mode='HTML'
        )
    
    elif text == "✉️ Adminga murojaat":
        await update.message.reply_text(
            "Adminga yubormoqchi bo'lgan xabaringizni kiriting:",
            reply_markup=back_button()
        )
        return ADMIN_MESSAGE

# Search handlers
async def search_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔎 Anime nomini kiriting:\n\n"
        "📌 Iltimos, anime nomini aniq va xatolarsiz kiriting:\n\n"
        "📝 Namuna: <code>Naruto Shippuden</code>",
        reply_markup=back_button(),
        parse_mode='HTML'
    )
    return SEARCH_NAME

async def handle_search_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_term = update.message.text
    results = db.search_anime_by_name(search_term)
    
    if results:
        for anime in results:
            caption = f"📺 <b>{anime['name']}</b> 📺\n"
            caption += "━━━━━━━━━━━━━━━━━━\n"
            caption += f"🎭 <b>Janr:</b> {anime['genre']}\n"
            caption += f"🎬 <b>Epizodlar:</b> {anime['episode']}\n"
            caption += f"📝 <b>Tavsif:</b> <i>{anime['description']}</i>\n"
            caption += "━━━━━━━━━━━━━━━━━━\n"
            caption += f"🔗 <b>Anime ID:</b> {anime['id']}"
            
            keyboard = [[
                InlineKeyboardButton("▶️ Tomosha qilish", url=f"https://t.me/{context.bot.username}?start={anime['id']}"),
                InlineKeyboardButton("Dasturchi", url="https://t.me/znxrofi")
            ]]
            
            await update.message.reply_photo(
                photo=anime['image'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "❌ Anime topilmadi!\n\n🔍 Iltimos, anime nomini to'g'ri kiriting yoki boshqa variantni sinab ko'ring.",
            reply_markup=back_button()
        )
    
    return ConversationHandler.END

async def search_by_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔎 Anime kodini kiriting!\n\n"
        "📌 Iltimos, anime kodini faqat raqamlarda kiriting:\n\n"
        "📝 Namuna: <code>99</code>",
        reply_markup=back_button(),
        parse_mode='HTML'
    )
    return SEARCH_CODE

async def handle_search_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        anime_id = int(update.message.text)
        anime = db.search_anime_by_id(anime_id)
        
        if anime:
            caption = f"📺 <b>{anime['name']}</b> 📺\n"
            caption += "━━━━━━━━━━━━━━━━━━\n"
            caption += f"🎭 <b>Janr:</b> {anime['genre']}\n"
            caption += f"🎬 <b>Epizodlar:</b> {anime['episode']}\n"
            caption += f"📝 <b>Tavsif:</b> <i>{anime['description']}</i>\n"
            caption += "━━━━━━━━━━━━━━━━━━\n"
            caption += f"🔗 <b>Anime ID:</b> {anime['id']}"
            
            keyboard = [[
                InlineKeyboardButton("▶️ Tomosha qilish", url=f"https://t.me/{context.bot.username}?start={anime['id']}"),
                InlineKeyboardButton("Dasturchi", url="https://t.me/znxrofi")
            ]]
            
            await update.message.reply_photo(
                photo=anime['image'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Anime topilmadi!",
                reply_markup=back_button()
            )
    except ValueError:
        await update.message.reply_text(
            "⚠️ Faqat raqam kiriting!",
            reply_markup=back_button()
        )
    
    return ConversationHandler.END

async def search_by_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔎 Anime janrini kiriting!\n\n"
        "📌 Masalan: Action, Comedy, Drama...",
        reply_markup=back_button()
    )
    return SEARCH_GENRE

async def handle_search_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    genre = update.message.text
    results = db.search_anime_by_genre(genre)
    
    if results:
        keyboard = []
        for anime in results:
            keyboard.append([InlineKeyboardButton(f"📺 {anime['name']}", callback_data=f"anime_{anime['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Ortga", callback_data="back_main")])
        
        await update.message.reply_text(
            f"🎭 {genre} janriga mos animelar:\n\n📌 Pastdan tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "❌ Bu janr bo'yicha anime topilmadi!",
            reply_markup=back_button()
        )
    
    return ConversationHandler.END

async def show_anime_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        anime_id = int(query.data.split('_')[1])
        anime = db.search_anime_by_id(anime_id)
        
        if anime:
            caption = f"📺 <b>{anime['name']}</b> 📺\n"
            caption += "━━━━━━━━━━━━━━━━━━\n"
            caption += f"🎭 <b>Janr:</b> {anime['genre']}\n"
            caption += f"🎬 <b>Epizodlar:</b> {anime['episode']}\n"
            caption += f"📝 <b>Tavsif:</b> <i>{anime['description']}</i>\n"
            caption += "━━━━━━━━━━━━━━━━━━\n"
            caption += f"🔗 <b>Anime ID:</b> {anime['id']}"
            
            keyboard = [[
                InlineKeyboardButton("▶️ Tomosha qilish", url=f"https://t.me/{context.bot.username}?start={anime['id']}"),
                InlineKeyboardButton("Dasturchi", url="https://t.me/znxrofi")
            ]]
            
            await query.message.reply_photo(
                photo=anime['image'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    except (ValueError, IndexError):
        await query.answer("Xatolik yuz berdi!", show_alert=True)

# Premium handlers
async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = db.get_user(user_id)
    
    if user['balance'] >= 5000:
        new_balance = user['balance'] - 5000
        vip_time = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
        
        db.update_user_balance(user_id, -5000)
        db.set_user_vip(user_id, vip_time)
        
        await query.edit_message_text(
            f"✅ Siz muvaffaqiyatli Premium + tarif obunasiga o'tdingiz! 🏆\n\n"
            f"📅 Obunangiz tugash sanasi: <b>{vip_time}</b>",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "⚠️ Sizning balancingizda yetarlicha mablag' mavjud emas! Iltimos, hisobingizni to'ldiring."
        )

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💳 Botga pul kiritish 💰\n\n"
        "📌 Quyidagi karta raqamiga kerakli summada pul tashlang va \"✅ To'lov qildim\" tugmasini bosing.\n"
        "📎 Qancha miqdorda pul kiritganingizni va to'lov chekini yuboring.\n\n"
        "💳 Karta raqami:\n"
        "<code>12345678</code>\n"
        "👤 Karta egasi: Otajonov O.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ To'lov qildim", callback_data="payment_done"),
            InlineKeyboardButton("🔙 Ortga", callback_data="back_main")
        ]]),
        parse_mode='HTML'
    )

async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💰 Qancha miqdorda to'lov qilganingizni kiriting:",
        reply_markup=back_button()
    )
    return PAYMENT_AMOUNT

async def handle_payment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        context.user_data['payment_amount'] = amount
        
        await update.message.reply_text(
            "📸 To'lov chekini rasm ko'rinishida yuboring:",
            reply_markup=back_button()
        )
        return PAYMENT_PHOTO
    except ValueError:
        await update.message.reply_text(
            "⚠️ Iltimos, faqat raqam kiriting:",
            reply_markup=back_button()
        )
        return PAYMENT_AMOUNT

async def handle_payment_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        amount = context.user_data['payment_amount']
        user_id = update.effective_user.id
        
        payment_id = db.add_payment(user_id, amount, photo)
        
        await update.message.reply_text(
            "✅ To'lovni tasdiqlash arizasi muvaffaqiyatli adminga yuborildi!"
        )
        
        # Send to admin
        keyboard = payment_confirmation_keyboard(payment_id)
        
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=f"👤 Foydalanuvchi: {user_id}\n"
                   f"💰 To'lov summasi: {amount} UZS\n"
                   f"📩 To'lovni tasdiqlash uchun ariza yubordi.\n"
                   f"✅ To'lovni tasdiqlaysizmi?",
            reply_markup=keyboard
        )
        
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "⚠️ Iltimos, faqat rasm yuboring:",
            reply_markup=back_button()
        )
        return PAYMENT_PHOTO

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    payment_id = int(query.data.split('_')[-1])
    
    # Ma'lumotlarni olish va yangilash bir xil connectionda
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # To'lov ma'lumotlarini olish
        cursor.execute('SELECT user_id, amount FROM payments WHERE id = ?', (payment_id,))
        payment = cursor.fetchone()
        
        if payment:
            user_id, amount = payment
            # Statusni yangilash
            cursor.execute('UPDATE payments SET status = ? WHERE id = ?', ('confirmed', payment_id))
            # Balansni yangilash
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            conn.commit()
            
            # Xabarlarni yuborish
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✅ To'lov tasdiqlandi! Foydalanuvchi {user_id} balansi {amount} UZS ga oshirildi."
            )
            
            await context.bot.send_message(
                user_id, 
                f"✅ To'lovingiz tasdiqlandi! Balansingiz {amount} UZS ga oshirildi."
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text="❌ To'lov topilmadi!"
            )
    except Exception as e:
        print(f"To'lov tasdiqlashda xato: {e}")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ To'lov tasdiqlashda xato: {str(e)}"
        )
    finally:
        conn.close()

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    payment_id = int(query.data.split('_')[-1])
    db.update_payment_status(payment_id, 'cancelled')
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="❌ To'lov bekor qilindi."
    )

# Admin message handlers
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    
    keyboard = [[
        InlineKeyboardButton("✍️ Javob berish", callback_data=f"reply_{user_id}")
    ]]
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Yangi xabar:\n\n👤 Foydalanuvchi ID: {user_id}\n💬 Xabar: {message}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await update.message.reply_text(
        "✅ Xabaringiz adminga yuborildi. Tez orada javob olasiz!",
        reply_markup=ask_question_keyboard()
    )
    return ConversationHandler.END

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[1])
    context.user_data['reply_user_id'] = user_id
    
    await query.message.reply_text("✍️ Foydalanuvchiga javob yozing:")
    return USER_MESSAGE_ID

async def handle_reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data['reply_user_id']
    message = update.message.text
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 Admin javobi:\n\n{message}",
            reply_markup=ask_question_keyboard()
        )
        
        await update.message.reply_text("✅ Javob foydalanuvchiga yuborildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xabar yuborishda xato: {str(e)}")
    
    return ConversationHandler.END

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("Adminga yubormoqchi bo'lgan xabaringizni kiriting:")
    return ADMIN_MESSAGE

# Admin panel handlers
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    await update.message.reply_text(
        "👨‍💼 Admin panelga xush kelibsiz!\nBu yerda botni boshqarishingiz mumkin.",
        reply_markup=admin_panel_keyboard()
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_count = db.get_user_count()
    
    await query.edit_message_text(
        f"💡 Statistika:\n\n👤 Barcha foydalanuvchilar: {user_count}",
        reply_markup=back_admin_button()
    )

# Anime settings handlers
async def anime_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🎥 Anime sozlamlari:\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=anime_settings_keyboard()
    )

# Anime qo'shish
async def add_anime_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        "🎥 Anime nomini kiriting:",
        reply_markup=back_admin_button()
    )
    return ADD_ANIME_NAME

async def add_anime_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_name'] = update.message.text
    await update.message.reply_text("💀 Anime qismlar sonini kiriting:", reply_markup=back_admin_button())
    return ADD_ANIME_EPISODE

async def add_anime_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        episode_count = int(update.message.text)
        context.user_data['anime_episode'] = episode_count
        await update.message.reply_text("🌍 Anime chiqarilgan davlatni kiriting:", reply_markup=back_admin_button())
        return ADD_ANIME_COUNTRY
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat son kiriting!", reply_markup=back_admin_button())
        return ADD_ANIME_EPISODE

async def add_anime_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_country'] = update.message.text
    await update.message.reply_text("🔦 Anime tilini kiriting:", reply_markup=back_admin_button())
    return ADD_ANIME_LANGUAGE

async def add_anime_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_language'] = update.message.text
    await update.message.reply_text("📜 Anime tavsifini kiriting:", reply_markup=back_admin_button())
    return ADD_ANIME_DESCRIPTION

async def add_anime_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_description'] = update.message.text
    await update.message.reply_text("🎭 Anime janrini kiriting:", reply_markup=back_admin_button())
    return ADD_ANIME_GENRE

async def add_anime_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_genre'] = update.message.text
    await update.message.reply_text("🖼 Anime rasmi yuboring:", reply_markup=back_admin_button())
    return ADD_ANIME_IMAGE

async def add_anime_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        
        try:
            anime_id = db.add_anime(
                context.user_data['anime_name'],
                context.user_data['anime_episode'],
                context.user_data['anime_country'],
                context.user_data['anime_language'],
                photo,
                context.user_data['anime_description'],
                context.user_data['anime_genre']
            )
            
            await update.message.reply_text(
                f"✅ Anime muvaffaqiyatli qo'shildi!\n\n🄚 Anime kodi: <code>{anime_id}</code>",
                parse_mode='HTML',
                reply_markup=back_admin_button()
            )
            
            context.user_data.clear()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}", reply_markup=back_admin_button())
        
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Iltimos, anime rasmini yuboring!", reply_markup=back_admin_button())
        return ADD_ANIME_IMAGE

# Qism qo'shish
async def add_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        "🔢 Anime ID sini kiriting:",
        reply_markup=back_admin_button()
    )
    return ADD_EPISODE_ANIME_ID

async def add_episode_anime_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        anime_id = int(update.message.text)
        anime = db.search_anime_by_id(anime_id)
        
        if anime:
            context.user_data['episode_anime_id'] = anime_id
            context.user_data['anime_name'] = anime['name']
            await update.message.reply_text(
                f"🎥 {anime['name']} uchun epizod videosini yuboring:",
                reply_markup=back_admin_button()
            )
            return ADD_EPISODE_FILE
        else:
            await update.message.reply_text("❌ Anime topilmadi! Qayta urinib ko'ring:", reply_markup=back_admin_button())
            return ADD_EPISODE_ANIME_ID
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting:", reply_markup=back_admin_button())
        return ADD_EPISODE_ANIME_ID

async def add_episode_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        anime_id = context.user_data['episode_anime_id']
        file_id = update.message.video.file_id
        
        try:
            # Get current episode count
            episodes = db.get_anime_episodes(anime_id)
            episode_number = len(episodes) + 1
            
            db.add_episode(anime_id, episode_number, file_id)
            
            await update.message.reply_text(
                f"✅ {context.user_data['anime_name']} uchun {episode_number}-qism yuklandi!\n\n"
                f"Keyingi epizodni yuklash uchun shunchaki yana video yuboring yoki 🔙 Ortga tugmasini bosing",
                reply_markup=back_admin_button()
            )
            
            return ADD_EPISODE_FILE
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}", reply_markup=back_admin_button())
            return ADD_EPISODE_FILE
    else:
        await update.message.reply_text("❌ Iltimos, faqat video yuboring!", reply_markup=back_admin_button())
        return ADD_EPISODE_FILE

# Anime tahrirlash
async def edit_anime_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        "✏️ Tahrirlamoqchi bo'lgan anime ID sini kiriting:",
        reply_markup=back_admin_button()
    )
    return EDIT_ANIME_SELECT

async def edit_anime_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        anime_id = int(update.message.text)
        anime = db.search_anime_by_id(anime_id)
        
        if anime:
            context.user_data['edit_anime_id'] = anime_id
            context.user_data['edit_anime'] = anime
            
            await update.message.reply_text(
                f"✏️ <b>{anime['name']}</b> animeni tahrirlash\n\n"
                f"Qaysi maydonni tahrirlamoqchisiz?",
                reply_markup=edit_anime_fields_keyboard(),
                parse_mode='HTML'
            )
            return EDIT_ANIME_FIELD
        else:
            await update.message.reply_text("❌ Anime topilmadi! Qayta urinib ko'ring:", reply_markup=back_admin_button())
            return EDIT_ANIME_SELECT
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting:", reply_markup=back_admin_button())
        return EDIT_ANIME_SELECT

async def edit_anime_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    field = query.data.replace('edit_field_', '')
    context.user_data['edit_field'] = field
    
    field_names = {
        'name': 'nomi',
        'episode': 'epizodlar soni',
        'country': 'davlati',
        'language': 'tili',
        'description': 'tavsifi',
        'genre': 'janri',
        'image': 'rasmi'
    }
    
    await query.edit_message_text(
        f"✏️ Anime {field_names[field]}ni kiriting:",
        reply_markup=back_admin_button()
    )
    return EDIT_ANIME_VALUE

async def edit_anime_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data['edit_field']
    anime_id = context.user_data['edit_anime_id']
    value = update.message.text
    
    try:
        if field == 'episode':
            value = int(value)
        
        db.update_anime(anime_id, field, value)
        
        await update.message.reply_text(
            f"✅ Anime {field} muvaffaqiyatli yangilandi!",
            reply_markup=back_admin_button()
        )
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}", reply_markup=back_admin_button())
        return EDIT_ANIME_VALUE

async def edit_anime_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        field = context.user_data['edit_field']
        anime_id = context.user_data['edit_anime_id']
        photo = update.message.photo[-1].file_id
        
        try:
            db.update_anime(anime_id, field, photo)
            
            await update.message.reply_text(
                f"✅ Anime {field} muvaffaqiyatli yangilandi!",
                reply_markup=back_admin_button()
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}", reply_markup=back_admin_button())
            return EDIT_ANIME_VALUE
    else:
        await update.message.reply_text("❌ Iltimos, rasm yuboring!", reply_markup=back_admin_button())
        return EDIT_ANIME_VALUE

# Anime ro'yxati
async def list_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    anime_list = db.get_all_anime()
    
    if not anime_list:
        await query.edit_message_text(
            "📭 Hozircha anime qo'shilmagan!",
            reply_markup=back_admin_button()
        )
        return
    
    text = "📋 Anime ro'yxati:\n\n"
    for anime in anime_list:
        text += f"🆔 {anime['id']} - {anime['name']}\n"
        text += f"   📺 {anime['episode']} qism | {anime['genre']}\n"
        text += f"   🌍 {anime['country']} | 🗣 {anime['language']}\n\n"
    
    await query.edit_message_text(
        text,
        reply_markup=back_admin_button()
    )

# Anime o'chirish
async def delete_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        "🗑 O'chirmoqchi bo'lgan anime ID sini kiriting:",
        reply_markup=back_admin_button()
    )
    return ConversationHandler.END

async def handle_delete_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        anime_id = int(update.message.text)
        anime = db.search_anime_by_id(anime_id)
        
        if anime:
            db.delete_anime(anime_id)
            await update.message.reply_text(
                f"✅ {anime['name']} animesi muvaffaqiyatli o'chirildi!",
                reply_markup=back_admin_button()
            )
        else:
            await update.message.reply_text("❌ Anime topilmadi!", reply_markup=back_admin_button())
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting!", reply_markup=back_admin_button())

# Channel settings handlers
async def channel_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📣 Kanallar sozlamalari:",
        reply_markup=channel_settings_keyboard()
    )

async def mandatory_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔐 Majburiy obuna kanallari:",
        reply_markup=mandatory_channels_keyboard()
    )

async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text("Kanal ID sini kiriting (-100 qo'ymasdan):", reply_markup=back_admin_button())
    return ADD_CHANNEL_ID

async def add_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_id'] = update.message.text
    await update.message.reply_text("Kanal havolasini kiriting (https://t.me bilan):", reply_markup=back_admin_button())
    return ADD_CHANNEL_LINK

async def add_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_link = update.message.text
    channel_id = context.user_data['channel_id']
    
    try:
        db.add_channel(channel_id, channel_link, 'request')
        await update.message.reply_text("✅ Kanal muvaffaqiyatli qo'shildi!", reply_markup=back_admin_button())
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}", reply_markup=back_admin_button())
    
    context.user_data.clear()
    return ConversationHandler.END

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    channels = db.get_channels('request')
    
    if not channels:
        await query.edit_message_text("📭 Majburiy obuna kanallari yo'q!", reply_markup=back_admin_button())
        return
    
    text = "📃 Majburiy obuna kanallari:\n\n"
    for i, channel in enumerate(channels):
        text += f"{i+1}. <a href='{channel['channel_link']}'>Kanal</a>\n"
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=back_admin_button()
    )

async def delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    channels = db.get_channels('request')
    
    if not channels:
        await query.edit_message_text("📭 O'chirish uchun kanal yo'q!", reply_markup=back_admin_button())
        return
    
    keyboard = []
    for i, channel in enumerate(channels):
        keyboard.append([InlineKeyboardButton(f"{i+1}. {channel['channel_link']}", callback_data=f"delete_channel_{channel['channel_id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")])
    
    await query.edit_message_text(
        "🗑 O'chirish uchun kanallarni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_channel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    channel_id = query.data.split('_')[-1]
    
    try:
        db.delete_channel(channel_id)
        await query.edit_message_text("✅ Kanal muvaffaqiyatli o'chirildi!", reply_markup=back_admin_button())
    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", reply_markup=back_admin_button())

# Anime channel setup
async def anime_channel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_channel = db.get_setting('anime_channel')
    await query.edit_message_text(
        f"🎥 Hozirgi anime kanali: {current_channel}\n\n"
        "Yangi anime kanalini kiriting (@ bilan):",
        reply_markup=back_admin_button()
    )
    return ANIME_CHANNEL_SETUP

async def handle_anime_channel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_channel = update.message.text
    db.update_setting('anime_channel', new_channel)
    
    await update.message.reply_text(f"✅ Anime kanali {new_channel} ga o'zgartirildi!", reply_markup=back_admin_button())
    return ConversationHandler.END

# Main settings handlers
async def main_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "⚙️ Asosiy sozlamalar bo'limiga xush kelibsiz!",
        reply_markup=main_settings_keyboard(db)
    )

async def toggle_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    share_status = db.get_setting('share')
    new_status = 'true' if share_status == 'false' else 'false'
    db.update_setting('share', new_status)
    
    status_text = "yoqildi" if new_status == 'true' else "o'chirildi"
    await query.edit_message_text(
        f"✅ Kino uzatish muvaffaqiyatli {status_text}!",
        reply_markup=main_settings_keyboard(db)
    )

async def start_text_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_text = db.get_setting('start_text')
    await query.edit_message_text(
        f"📝 Hozirgi start matni:\n{current_text}\n\nYangi start matnini kiriting:",
        reply_markup=back_admin_button()
    )
    return START_TEXT_SETUP

async def handle_start_text_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    db.update_setting('start_text', new_text)
    
    await update.message.reply_text("✅ Start matni muvaffaqiyatli o'zgartirildi!", reply_markup=back_admin_button())
    return ConversationHandler.END

async def help_text_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_text = db.get_setting('help_text')
    await query.edit_message_text(
        f"ℹ️ Hozirgi yordam matni:\n{current_text}\n\nYangi yordam matnini kiriting:",
        reply_markup=back_admin_button()
    )
    return HELP_TEXT_SETUP

async def handle_help_text_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    db.update_setting('help_text', new_text)
    
    await update.message.reply_text("✅ Yordam matni muvaffaqiyatli o'zgartirildi!", reply_markup=back_admin_button())
    return ConversationHandler.END

async def ads_text_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_text = db.get_setting('ads_text')
    await query.edit_message_text(
        f"📢 Hozirgi reklama matni:\n{current_text}\n\nYangi reklama matnini kiriting:",
        reply_markup=back_admin_button()
    )
    return ADS_TEXT_SETUP

async def handle_ads_text_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    db.update_setting('ads_text', new_text)
    
    await update.message.reply_text("✅ Reklama matni muvaffaqiyatli o'zgartirildi!", reply_markup=back_admin_button())
    return ConversationHandler.END

async def bot_situation_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    situation = db.get_setting('situation')
    situation_text = "Yoqilgan ✅" if situation == 'On' else "O'chirilgan ❌"
    button_text = "O'chirish ❌" if situation == 'On' else "Yoqish ✅"
    
    await query.edit_message_text(
        f"🤖 Bot holati: {situation_text}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(button_text, callback_data="toggle_bot_situation")],
            [InlineKeyboardButton("🔙 Ortga", callback_data="back_admin")]
        ])
    )

async def toggle_bot_situation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    situation = db.get_setting('situation')
    new_situation = 'Off' if situation == 'On' else 'On'
    db.update_setting('situation', new_situation)
    
    situation_text = "o'chirildi" if new_situation == 'Off' else "yoqildi"
    await query.edit_message_text(
        f"✅ Bot muvaffaqiyatli {situation_text}!",
        reply_markup=back_admin_button()
    )

# Create post handler
async def create_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("📺 Anime ID sini kiriting:", reply_markup=back_admin_button())

async def handle_create_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        anime_id = int(update.message.text)
        anime = db.search_anime_by_id(anime_id)
        
        if anime:
            caption = f"📺 *{anime['name']}* 📺\n"
            caption += "┏━━━━━━━━━━━━━━━┓\n"
            caption += f"┃ 🎞 *Qismlar:* {anime['episode']}\n"
            caption += f"┃ 🌍 *Davlat:* {anime['country']}\n"
            caption += f"┃ 🗣 *Til:* {anime['language']}\n"
            caption += f"┃ 🔖 *Janr:* {anime['genre']}\n"
            caption += f"┃ ⭐ *Reyting:* {anime['rating']}\n"
            caption += "┗━━━━━━━━━━━━━━━┛\n"
            caption += f"📌 *Tavsif:* {anime['description']}"
            
            anime_channel = db.get_setting('anime_channel')
            keyboard = [[
                InlineKeyboardButton(f"{anime_channel} ga yuborish", callback_data=f"send_post_{anime_id}")
            ]]
            
            await update.message.reply_photo(
                photo=anime['image'],
                caption=caption,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("❌ Ushbu ID bilan anime topilmadi!", reply_markup=back_admin_button())
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting!", reply_markup=back_admin_button())

async def send_post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    anime_id = int(query.data.split('_')[-1])
    anime = db.search_anime_by_id(anime_id)
    
    if anime:
        caption = f"📺 *{anime['name']}* 📺\n"
        caption += "┏━━━━━━━━━━━━━━━┓\n"
        caption += f"┃ 🎞 *Qismlar:* {anime['episode']}\n"
        caption += f"┃ 🌍 *Davlat:* {anime['country']}\n"
        caption += f"┃ 🗣 *Til:* {anime['language']}\n"
        caption += f"┃ 🔖 *Janr:* {anime['genre']}\n"
        caption += f"┃ ⭐ *Reyting:* {anime['rating']}\n"
        caption += "┗━━━━━━━━━━━━━━━┛\n"
        caption += f"📌 *Tavsif:* {anime['description']}"
        
        anime_channel = db.get_setting('anime_channel')
        try:
            await context.bot.send_photo(
                chat_id=anime_channel,
                photo=anime['image'],
                caption=caption,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔷 Tomosha qilish 🔷", url=f"https://t.me/{context.bot.username}?start={anime_id}")
                ]])
            )
            await query.edit_message_text("✅ Postingiz muvaffaqiyatli kanalga yuborildi!", reply_markup=back_admin_button())
        except Exception as e:
            await query.edit_message_text(f"❌ Xatolik: {str(e)}", reply_markup=back_admin_button())

# Send message handlers
async def send_message_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "✉️ Xabar yuborish menyusi:",
        reply_markup=send_message_keyboard()
    )

async def user_message_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text("Foydalanuvchi ID sini kiriting:", reply_markup=back_admin_button())
    return USER_MESSAGE_ID

async def broadcast_message_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("Hamma foydalanuvchilarga yuboriladigan xabarni kiriting:", reply_markup=back_admin_button())
    return BROADCAST_MESSAGE

async def forward_message_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("Forward qilinadigan xabarni yuboring:", reply_markup=back_admin_button())
    return FORWARD_MESSAGE

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        context.user_data['target_user_id'] = user_id
        await update.message.reply_text("Foydalanuvchiga yuboriladigan xabarni kiriting:", reply_markup=back_admin_button())
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting!", reply_markup=back_admin_button())
        return USER_MESSAGE_ID

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    users = db.get_all_users()
    
    sent = 0
    total = len(users)
    
    status_msg = await update.message.reply_text(f"Xabar yuborish boshlandi:\nYuborildi: 0/{total}")
    
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
            sent += 1
            if sent % 10 == 0:
                await status_msg.edit_text(f"Xabar yuborish boshlandi:\nYuborildi: {sent}/{total}")
            await asyncio.sleep(0.1)
        except:
            continue
    
    await status_msg.edit_text(f"Xabar yuborish yakunlandi:\nYuborildi: {sent}/{total}")
    return ConversationHandler.END

async def handle_forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_id = update.message.message_id
    users = db.get_all_users()
    
    sent = 0
    total = len(users)
    
    status_msg = await update.message.reply_text(f"Forward xabar yuborish boshlandi:\nYuborildi: 0/{total}")
    
    for user_id in users:
        try:
            await context.bot.forward_message(
                chat_id=user_id,
                from_chat_id=update.effective_chat.id,
                message_id=message_id
            )
            sent += 1
            if sent % 10 == 0:
                await status_msg.edit_text(f"Forward xabar yuborish boshlandi:\nYuborildi: {sent}/{total}")
            await asyncio.sleep(0.1)
        except:
            continue
    
    await status_msg.edit_text(f"Forward xabar yuborish yakunlandi:\nYuborildi: {sent}/{total}")
    return ConversationHandler.END

# Back handlers - BU YERDA ASOSIY ORQAGA QAYTISH HANDLERLARI
async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    start_text = db.get_setting('start_text')
    await query.edit_message_text(
        start_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )
    return ConversationHandler.END

async def back_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👨‍💼 Admin panelga xush kelibsiz!\nBu yerda botni boshqarishingiz mumkin.",
        reply_markup=admin_panel_keyboard()
    )
    return ConversationHandler.END

async def back_to_anime_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🎥 Anime sozlamlari:\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=anime_settings_keyboard()
    )
    return ConversationHandler.END

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if await check_subscription(user_id, context):
        start_text = db.get_setting('start_text')
        await query.edit_message_text(
            start_text,
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Amal bekor qilindi.",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatolarni log qilish"""
    logging.error(f"Xato yuz berdi: {context.error}", exc_info=context.error)

def main():
    # Set up logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("panel", admin_panel))
    
    # ANIME SETTINGS HANDLERLARINI QO'SHISH
    application.add_handler(CallbackQueryHandler(anime_settings, pattern="^anime_settings$"))
    application.add_handler(CallbackQueryHandler(back_to_anime_settings, pattern="^back_to_anime_settings$"))
    
    # Search conversation
    search_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(search_by_name, pattern="^search_name$"),
            CallbackQueryHandler(search_by_code, pattern="^search_code$"),
            CallbackQueryHandler(search_by_genre, pattern="^search_genre$")
        ],
        states={
            SEARCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_name)],
            SEARCH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_code)],
            SEARCH_GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_genre)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_main, pattern="^back_main$")
        ]
    )
    application.add_handler(search_conv)
    
    # Add anime conversation
    add_anime_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_anime_start, pattern="^add_anime$")],
        states={
            ADD_ANIME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_anime_name)],
            ADD_ANIME_EPISODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_anime_episode)],
            ADD_ANIME_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_anime_country)],
            ADD_ANIME_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_anime_language)],
            ADD_ANIME_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_anime_description)],
            ADD_ANIME_GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_anime_genre)],
            ADD_ANIME_IMAGE: [MessageHandler(filters.PHOTO, add_anime_image)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_anime_settings, pattern="^back_admin$|^back_to_anime_settings$")
        ]
    )
    application.add_handler(add_anime_conv)
    
    # Add episode conversation
    add_episode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_episode_start, pattern="^add_episode$")],
        states={
            ADD_EPISODE_ANIME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_episode_anime_id)],
            ADD_EPISODE_FILE: [MessageHandler(filters.VIDEO, add_episode_file)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_anime_settings, pattern="^back_admin$|^back_to_anime_settings$")
        ]
    )
    application.add_handler(add_episode_conv)
    
    # Edit anime conversation
    edit_anime_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_anime_start, pattern="^edit_anime$")],
        states={
            EDIT_ANIME_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_anime_select)],
            EDIT_ANIME_FIELD: [CallbackQueryHandler(edit_anime_field, pattern="^edit_field_")],
            EDIT_ANIME_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_anime_value),
                MessageHandler(filters.PHOTO, edit_anime_image)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_anime_settings, pattern="^back_admin$|^back_to_anime_settings$")
        ]
    )
    application.add_handler(edit_anime_conv)
    
    # Payment conversation
    payment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(payment_done, pattern="^payment_done$")],
        states={
            PAYMENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment_amount)],
            PAYMENT_PHOTO: [MessageHandler(filters.PHOTO, handle_payment_photo)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_main, pattern="^back_main$")
        ]
    )
    application.add_handler(payment_conv)
    
    # Admin message conversation
    admin_msg_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^✉️ Adminga murojaat$"), handle_message),
            CallbackQueryHandler(ask_question, pattern="^ask_question$")
        ],
        states={
            ADMIN_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_main, pattern="^back_main$")
        ]
    )
    application.add_handler(admin_msg_conv)
    
    # Reply to user conversation
    reply_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(reply_to_user, pattern="^reply_")],
        states={
            USER_MESSAGE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_to_user)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(reply_conv)
    
    # Add channel conversation
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern="^add_channel$")],
        states={
            ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_id)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_link)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(add_channel_conv)
    
    # Settings conversations
    anime_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(anime_channel_setup, pattern="^anime_channel_setup$")],
        states={
            ANIME_CHANNEL_SETUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_anime_channel_setup)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(anime_channel_conv)
    
    start_text_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_text_setup, pattern="^start_text_setup$")],
        states={
            START_TEXT_SETUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_start_text_setup)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(start_text_conv)
    
    help_text_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(help_text_setup, pattern="^help_text_setup$")],
        states={
            HELP_TEXT_SETUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_help_text_setup)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(help_text_conv)
    
    ads_text_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ads_text_setup, pattern="^ads_text_setup$")],
        states={
            ADS_TEXT_SETUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ads_text_setup)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(ads_text_conv)
    
    # Send message conversations
    user_msg_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(user_message_start, pattern="^user_message$")],
        states={
            USER_MESSAGE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(user_msg_conv)
    
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_message_start, pattern="^broadcast_message$")],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(broadcast_conv)
    
    forward_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(forward_message_start, pattern="^forward_message$")],
        states={
            FORWARD_MESSAGE: [MessageHandler(filters.ALL, handle_forward_message)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_admin, pattern="^back_admin$")
        ]
    )
    application.add_handler(forward_conv)
    
    # POST TAYYORLASH HANDLERLARI - YANGI QO'SHILDI
    application.add_handler(CallbackQueryHandler(create_post, pattern="^create_post$"))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+$') & filters.Chat(ADMIN_ID), handle_create_post))
    application.add_handler(CallbackQueryHandler(send_post_to_channel, pattern="^send_post_"))
    
    # Other handlers - BU YERDA BARCA CALLBACK HANDLERLAR
    application.add_handler(CallbackQueryHandler(show_anime_details, pattern="^anime_"))
    application.add_handler(CallbackQueryHandler(buy_premium, pattern="^buy_premium$"))
    application.add_handler(CallbackQueryHandler(add_money, pattern="^add_money$"))
    application.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    application.add_handler(CallbackQueryHandler(back_admin, pattern="^back_admin$"))
    application.add_handler(CallbackQueryHandler(back_to_anime_settings, pattern="^back_to_anime_settings$"))
    application.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(anime_settings, pattern="^anime_settings$"))
    application.add_handler(CallbackQueryHandler(channel_settings, pattern="^channel_settings$"))
    application.add_handler(CallbackQueryHandler(main_settings, pattern="^main_settings$"))
    application.add_handler(CallbackQueryHandler(mandatory_subscriptions, pattern="^mandatory_subscriptions$"))
    application.add_handler(CallbackQueryHandler(list_channels, pattern="^list_channels$"))
    application.add_handler(CallbackQueryHandler(delete_channel, pattern="^delete_channel$"))
    application.add_handler(CallbackQueryHandler(delete_channel_confirm, pattern="^delete_channel_"))
    application.add_handler(CallbackQueryHandler(toggle_share, pattern="^toggle_share$"))
    application.add_handler(CallbackQueryHandler(bot_situation_setup, pattern="^bot_situation_setup$"))
    application.add_handler(CallbackQueryHandler(toggle_bot_situation, pattern="^toggle_bot_situation$"))
    application.add_handler(CallbackQueryHandler(send_message_menu, pattern="^send_message$"))
    application.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_payment_"))
    application.add_handler(CallbackQueryHandler(cancel_payment, pattern="^cancel_payment_"))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(list_anime, pattern="^list_anime$"))
    
    # Delete anime handler
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+$') & filters.Chat(ADMIN_ID), handle_delete_anime))
    
    # Main menu handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

# BU QATIR BOSHIDA BO'LISHI KERAK
if __name__ == '__main__':
    main()
    
# bu qodni shaxshsan znxrofi terib chiqan agar manbasiz o'girlansa sikaman ko'd o'zgarmasin    