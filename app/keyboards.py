from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

TEXTS = {
    'uz': {
        'search':    '🔎 Anime izlash',
        'premium':   '💎 Premium +',
        'profile':   '👤 Hisobim',
        'contact':   '✉️ Adminga murojaat',
        'watchlist': '📌 Ro\'yxatim',
        'history':   '🕓 Tarix',
        'top':       '🏆 Top anime',
        'for_you':   '✨ Siz uchun',
        'missions':  '🎮 Missiyalar',
        'shorts':    '🎬 Shorts',
        'assistant': '🤖 AI Assistant',
        'dna':       '🧬 DNA Profil',
    },
    'ru': {
        'search':    '🔎 Поиск аниме',
        'premium':   '💎 Premium +',
        'profile':   '👤 Мой профиль',
        'contact':   '✉️ Написать админу',
        'watchlist': '📌 Мой список',
        'history':   '🕓 История',
        'top':       '🏆 Топ аниме',
        'for_you':   '✨ Для вас',
        'missions':  '🎮 Миссии',
        'shorts':    '🎬 Shorts',
        'assistant': '🤖 AI Ассистент',
        'dna':       '🧬 DNA Профиль',
    },
    'en': {
        'search':    '🔎 Search anime',
        'premium':   '💎 Premium +',
        'profile':   '👤 My profile',
        'contact':   '✉️ Contact admin',
        'watchlist': '📌 My watchlist',
        'history':   '🕓 History',
        'top':       '🏆 Top anime',
        'for_you':   '✨ For You',
        'missions':  '🎮 Missions',
        'shorts':    '🎬 Shorts',
        'assistant': '🤖 AI Assistant',
        'dna':       '🧬 DNA Profile',
    },
}

ALL_GENRES = [
    "Action", "Adventure", "Comedy", "Drama", "Fantasy",
    "Horror", "Mystery", "Romance", "Sci-Fi", "Slice of Life",
    "Sports", "Supernatural", "Thriller", "Mecha", "Isekai"
]

def main_menu_keyboard(lang='uz') -> ReplyKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS['uz'])
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text=t['for_you']),    KeyboardButton(text=t['search']))
    kb.row(KeyboardButton(text=t['shorts']),     KeyboardButton(text=t['top']))
    kb.row(KeyboardButton(text=t['missions']),   KeyboardButton(text=t['dna']))
    kb.row(KeyboardButton(text=t['watchlist']),  KeyboardButton(text=t['history']))
    kb.row(KeyboardButton(text=t['assistant']),  KeyboardButton(text=t['premium']))
    kb.row(KeyboardButton(text=t['profile']),    KeyboardButton(text=t['contact']))
    return kb.as_markup(resize_keyboard=True)

def get_menu_texts(lang='uz'):
    return TEXTS.get(lang, TEXTS['uz'])

def language_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
    )
    return kb.as_markup()

def genre_select_keyboard(selected: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for genre in ALL_GENRES:
        mark = "✅" if genre in selected else "☑️"
        kb.row(InlineKeyboardButton(text=f"{mark} {genre}", callback_data=f"genre_toggle_{genre}"))
    kb.row(InlineKeyboardButton(text="✔️ Tayyor", callback_data="genre_done"))
    return kb.as_markup()

def search_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🗞 Nom orqali",  callback_data="search_name"),
        InlineKeyboardButton(text="🔢 Kod orqali",  callback_data="search_code")
    )
    kb.row(InlineKeyboardButton(text="💎 Janr orqali", callback_data="search_genre"))
    kb.row(InlineKeyboardButton(text="🔙 Ortga",       callback_data="back_main"))
    return kb.as_markup()

def anime_detail_keyboard(bot_username: str, anime_id: int,
                          in_watchlist: bool, is_vip=False, has_clips=False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="▶️ Tomosha qilish",
        url=f"https://t.me/{bot_username}?start={anime_id}"
    ))
    wl_text = "🔕 Kuzatuvdan chiqarish" if in_watchlist else "🔔 Kuzatuvga qo'shish"
    kb.row(
        InlineKeyboardButton(text=wl_text,       callback_data=f"watchlist_toggle_{anime_id}"),
        InlineKeyboardButton(text="⭐ Baho ber",  callback_data=f"rate_anime_{anime_id}")
    )
    if has_clips:
        kb.row(InlineKeyboardButton(text="🎬 Shorts ko'r", callback_data=f"clips_anime_{anime_id}"))
    kb.row(InlineKeyboardButton(text="💬 Kommentlar", callback_data=f"comments_{anime_id}"))
    kb.row(InlineKeyboardButton(text="💬 Sharhlar", callback_data=f"reviews_{anime_id}"))
    if is_vip:
        kb.row(InlineKeyboardButton(text="💎 VIP — Premium kerak", callback_data="premium_info"))
    kb.row(InlineKeyboardButton(text="Dasturchi", url="https://t.me/znxrofi"))
    return kb.as_markup()

def rating_keyboard(anime_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    stars = ["1⭐","2⭐","3⭐","4⭐","5⭐","6⭐","7⭐","8⭐","9⭐","10⭐"]
    row = []
    for i, s in enumerate(stars, 1):
        row.append(InlineKeyboardButton(text=s, callback_data=f"give_rating_{anime_id}_{i}"))
        if len(row) == 5:
            kb.row(*row); row = []
    if row: kb.row(*row)
    kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_main"))
    return kb.as_markup()

def review_ask_keyboard(anime_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✍️ Sharh yozish",    callback_data=f"write_review_{anime_id}"),
        InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="back_main")
    )
    return kb.as_markup()

def episode_keyboard(anime_id: int, episode_number: int, total_episodes: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    nav = []
    if episode_number > 1:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"ep_{anime_id}_{episode_number-1}"))
    if episode_number < total_episodes:
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"ep_{anime_id}_{episode_number+1}"))
    if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text="⭐ Baho ber", callback_data=f"rate_anime_{anime_id}"))
    return kb.as_markup()

def inline_watch_keyboard(bot_username: str, anime_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="▶️ Tomosha qilish",
        url=f"https://t.me/{bot_username}?start={anime_id}"
    ))
    return kb.as_markup()

def profile_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📰 Activity feed",        callback_data="activity_feed"))
    kb.row(InlineKeyboardButton(text="➕ Pul kiritish",         callback_data="add_money"))
    kb.row(InlineKeyboardButton(text="🔗 Referral link",        callback_data="referral_link"))
    kb.row(InlineKeyboardButton(text="🧬 DNA Profil",           callback_data="my_dna"))
    kb.row(InlineKeyboardButton(text="🏆 Liderlar",             callback_data="leaderboard"))
    kb.row(InlineKeyboardButton(text="🌐 Tilni o'zgartirish",   callback_data="change_language"))
    kb.row(InlineKeyboardButton(text="🔙 Ortga",                callback_data="back_main"))
    return kb.as_markup()


def user_profile_keyboard(target_user_id: int, is_following: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if is_following:
        kb.row(InlineKeyboardButton(text="➖ Unfollow", callback_data=f"unfollow_{target_user_id}"))
    else:
        kb.row(InlineKeyboardButton(text="➕ Follow", callback_data=f"follow_{target_user_id}"))
    kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_main"))
    return kb.as_markup()

def premium_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💎 Premium haqida batafsil", callback_data="premium_info"))
    kb.row(InlineKeyboardButton(text="💳 Sotib olish",             callback_data="buy_premium"))
    kb.row(InlineKeyboardButton(text="🔙 Ortga",                   callback_data="back_main"))
    return kb.as_markup()

def payment_confirmation_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Tasdiqlash",   callback_data=f"confirm_payment_{payment_id}"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel_payment_{payment_id}")
    )
    return kb.as_markup()

def ask_question_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✉️ Yana savol berish", callback_data="ask_question"))
    return kb.as_markup()

def back_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_main"))
    return kb.as_markup()

def back_admin_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_admin"))
    return kb.as_markup()

def admin_panel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🔧 Asosiy sozlamalar",  callback_data="main_settings"),
        InlineKeyboardButton(text="🎥 Anime sozlamalari",  callback_data="anime_settings")
    )
    kb.row(
        InlineKeyboardButton(text="📝 Post tayyorlash",    callback_data="create_post"),
        InlineKeyboardButton(text="📣 Kanallar",           callback_data="channel_settings")
    )
    kb.row(
        InlineKeyboardButton(text="📈 Statistika",         callback_data="stats"),
        InlineKeyboardButton(text="✉️ Xabar yuborish",    callback_data="send_message")
    )
    kb.row(
        InlineKeyboardButton(text="📅 Rejalashtirilgan",   callback_data="scheduled_posts"),
        InlineKeyboardButton(text="🎬 Clips boshqaruv",    callback_data="clips_admin")
    )
    kb.row(
        InlineKeyboardButton(text="🧪 A/B Test natijalari",callback_data="ab_test_stats"),
        InlineKeyboardButton(text="⚙️ API sozlamalar",     callback_data="api_settings")
    )
    return kb.as_markup()

def anime_settings_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🎥 Anime qo'shish",   callback_data="add_anime"),
        InlineKeyboardButton(text="📀 Qism qo'shish",    callback_data="add_episode")
    )
    kb.row(
        InlineKeyboardButton(text="✏️ Anime tahrirlash", callback_data="edit_anime"),
        InlineKeyboardButton(text="🎬 Qism tahrirlash",  callback_data="edit_episode")
    )
    kb.row(
        InlineKeyboardButton(text="🗑 Anime o'chirish",  callback_data="delete_anime"),
        InlineKeyboardButton(text="📋 Anime ro'yxati",   callback_data="list_anime")
    )
    kb.row(InlineKeyboardButton(text="🔙 Ortga",          callback_data="back_admin"))
    return kb.as_markup()

def channel_settings_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔐 Majburiy obunalar",  callback_data="mandatory_subscriptions"))
    kb.row(InlineKeyboardButton(text="🎥 Anime kanal",         callback_data="anime_channel_setup"))
    kb.row(InlineKeyboardButton(text="🔙 Ortga",              callback_data="back_admin"))
    return kb.as_markup()

def main_settings_keyboard(db) -> InlineKeyboardMarkup:
    share_status = db.get_setting('share')
    share_text = "✅ Uzatish yoqish" if share_status == "false" else "❌ Uzatish o'chirish"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=share_text, callback_data="toggle_share"))
    kb.row(
        InlineKeyboardButton(text="📝 Start matni",  callback_data="start_text_setup"),
        InlineKeyboardButton(text="🤖 Bot holati",   callback_data="bot_situation_setup")
    )
    kb.row(
        InlineKeyboardButton(text="ℹ️ Yordam matni", callback_data="help_text_setup"),
        InlineKeyboardButton(text="📢 Reklama matni",callback_data="ads_text_setup")
    )
    kb.row(
        InlineKeyboardButton(text="💎 Premium narx", callback_data="premium_price_setup"),
        InlineKeyboardButton(text="🎁 Referral bonus",callback_data="referral_bonus_setup")
    )
    kb.row(InlineKeyboardButton(text="🔙 Ortga",      callback_data="back_admin"))
    return kb.as_markup()

def mandatory_channels_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Qo'shish", callback_data="add_channel"))
    kb.row(
        InlineKeyboardButton(text="📃 Ro'yxat",   callback_data="list_channels"),
        InlineKeyboardButton(text="🗑 O'chirish",  callback_data="delete_channel")
    )
    kb.row(InlineKeyboardButton(text="🔙 Ortga",   callback_data="back_admin"))
    return kb.as_markup()

def send_message_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="👤 Userga",         callback_data="user_message"))
    kb.row(InlineKeyboardButton(text="👥 Oddiy xabar",    callback_data="broadcast_message"))
    kb.row(InlineKeyboardButton(text="📩 Forward xabar",  callback_data="forward_message"))
    kb.row(InlineKeyboardButton(text="🔙 Ortga",          callback_data="back_admin"))
    return kb.as_markup()

def edit_anime_fields_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for text, cb in [
        ("📝 Nomi","edit_field_name"),("🎬 Epizodlar soni","edit_field_episode"),
        ("🌍 Davlati","edit_field_country"),("🗣 Tili","edit_field_language"),
        ("📖 Tavsifi","edit_field_description"),("🎭 Janri","edit_field_genre"),
        ("🖼 Rasm","edit_field_image"),("💎 VIP","edit_field_is_vip"),
        ("⚡ Early Access","edit_field_early_access"),
    ]:
        kb.row(InlineKeyboardButton(text=text, callback_data=cb))
    kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="anime_settings"))
    return kb.as_markup()

def scheduled_posts_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Yangi rejalashtirish",   callback_data="schedule_new_post"))
    kb.row(InlineKeyboardButton(text="📋 Rejalashtirilgan postlar", callback_data="list_scheduled"))
    kb.row(InlineKeyboardButton(text="🔙 Ortga",                   callback_data="back_admin"))
    return kb.as_markup()