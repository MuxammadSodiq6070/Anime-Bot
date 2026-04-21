import asyncio
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    InlineQueryResultPhoto
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Database
from keyboards import (
    main_menu_keyboard, search_keyboard, back_button,
    premium_keyboard, profile_keyboard, payment_confirmation_keyboard,
    ask_question_keyboard, language_keyboard, genre_select_keyboard,
    anime_detail_keyboard, rating_keyboard, review_ask_keyboard,
    episode_keyboard, inline_watch_keyboard, get_menu_texts
)

router = Router()


# ── FSM States ─────────────────────────────────────────────────────────────────
class SearchStates(StatesGroup):
    search_name  = State()
    search_code  = State()
    search_genre = State()

class PaymentStates(StatesGroup):
    amount = State()
    photo  = State()

class ContactAdminState(StatesGroup):
    message = State()

class ReplyUserState(StatesGroup):
    message = State()

class RatingState(StatesGroup):
    review = State()

class GenreOnboarding(StatesGroup):
    selecting = State()


# ── Helpers ────────────────────────────────────────────────────────────────────
async def check_subscription(user_id: int, bot: Bot, db: Database) -> bool:
    channels = db.get_channels('request')
    if not channels:
        return True
    kb = InlineKeyboardBuilder()
    not_subscribed = False
    for i, channel in enumerate(channels):
        try:
            ch_id = channel['channel_id']
            if not ch_id.startswith('-100'):
                ch_id = f"-100{ch_id}"
            member = await bot.get_chat_member(chat_id=int(ch_id), user_id=user_id)
            subscribed = member.status in ('creator', 'administrator', 'member')
        except Exception as e:
            subscribed = False
        title = channel['channel_link'].split('/')[-1] if channel['channel_link'] else f"Kanal {i+1}"
        btn_text = f"✅ {title}" if subscribed else f"❌ {title}"
        if channel['channel_link']:
            kb.row(InlineKeyboardButton(text=btn_text, url=channel['channel_link']))
        else:
            kb.row(InlineKeyboardButton(text=btn_text, callback_data="no_link"))
        if not subscribed:
            not_subscribed = True
    kb.row(InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_subscription"))
    if not_subscribed:
        await bot.send_message(
            chat_id=user_id,
            text="⚠️ <b>Botdan to'liq foydalanish uchun kanallarga obuna bo'ling!</b>",
            reply_markup=kb.as_markup(), parse_mode='HTML'
        )
        return False
    return True


def get_lang(db, user_id):
    user = db.get_user(user_id)
    return user.get('language', 'uz') if user else 'uz'


def anime_caption_html(anime: dict) -> str:
    vip_badge = " 💎 VIP" if anime.get('is_vip') else ""
    return (
        f"📺 <b>{anime['name']}</b>{vip_badge}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎭 <b>Janr:</b> {anime['genre']}\n"
        f"🎬 <b>Epizodlar:</b> {anime['episode']}\n"
        f"🌍 <b>Davlat:</b> {anime.get('country','')}\n"
        f"⭐ <b>Reyting:</b> {anime['rating']}/10\n"
        f"👁 <b>Ko'rishlar:</b> {anime.get('views',0)}\n"
        f"📝 <b>Tavsif:</b> <i>{anime['description']}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Anime ID:</b> {anime['id']}"
    )


# ── Register ───────────────────────────────────────────────────────────────────
def register_user_handlers(router: Router, db: Database, admin_id: int):

    # ── /start ─────────────────────────────────────────────────────────────────
    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext):
        await state.clear()
        user = message.from_user
        is_new = db.is_new_user(user.id)

        # Referral link tekshirish: /start ref_12345
        referral_by = None
        args = message.text.split()
        if len(args) > 1:
            arg = args[1]
            if arg.startswith("ref_"):
                try:
                    referral_by = int(arg.split("_")[1])
                    if referral_by == user.id:
                        referral_by = None
                except ValueError:
                    pass

        db.add_user(user.id, user.username, user.first_name, user.last_name, referral_by)

        # Referral bonus berish
        if is_new and referral_by:
            bonus = int(db.get_setting('referral_bonus') or 100)
            db.update_user_balance(referral_by, bonus)
            try:
                await message.bot.send_message(
                    chat_id=referral_by,
                    text=f"🎉 Do'stingiz <b>{user.first_name}</b> botga qo'shildi!\n"
                         f"💰 Sizga <b>{bonus} UZS</b> bonus berildi!",
                    parse_mode='HTML'
                )
            except Exception:
                pass

        situation = db.get_setting('situation')
        if situation == 'Off' and user.id != admin_id:
            await message.answer(
                "⚠️ <b>Bot vaqtincha ishlamayapti!</b>\n\n"
                "<i>Hozirda texnik ishlar olib borilmoqda.</i>",
                parse_mode='HTML'
            )
            return

        if not await check_subscription(user.id, message.bot, db):
            return

        # Yangi foydalanuvchi — til tanlash
        if is_new:
            await message.answer(
                "🌐 <b>Tilni tanlang / Выберите язык / Choose language:</b>",
                reply_markup=language_keyboard(), parse_mode='HTML'
            )
            return

        # Anime ID orqali kelgan
        if len(args) > 1 and not args[1].startswith("ref_"):
            try:
                anime_id = int(args[1])
                await _send_anime_episodes(message, db, anime_id)
                return
            except ValueError:
                pass

        lang = get_lang(db, user.id)
        # Janr preferenslari yo'q bo'lsa onboarding
        if is_new and not db.has_genre_preferences(user.id):
            await state.set_state(GenreOnboarding.selecting)
            await state.update_data(selected_genres=[])
            await message.answer(
                "🎭 <b>Qaysi janrlarni yaxshi ko'rasiz?</b>\n"
                "Ko'proq tanlasangiz, tavsiyalar aniqroq bo'ladi:",
                reply_markup=genre_select_keyboard([]),
                parse_mode='HTML'
            )
            return

        start_text = db.get_setting('start_text')
        await message.answer(start_text, reply_markup=main_menu_keyboard(lang), parse_mode='HTML')

    # ── Language selection ─────────────────────────────────────────────────────
    @router.callback_query(F.data.startswith("lang_"))
    async def set_language(call: CallbackQuery, state: FSMContext):
        lang = call.data.split("_")[1]
        db.set_user_language(call.from_user.id, lang)
        await call.answer("✅")

        # Genre onboarding
        if not db.has_genre_preferences(call.from_user.id):
            await state.set_state(GenreOnboarding.selecting)
            await state.update_data(selected_genres=[])
            await call.message.edit_text(
                "🎭 <b>Qaysi janrlarni yaxshi ko'rasiz?</b>\n"
                "Ko'proq tanlasangiz, tavsiyalar aniqroq bo'ladi:",
                reply_markup=genre_select_keyboard([]),
                parse_mode='HTML'
            )
        else:
            start_text = db.get_setting('start_text')
            await call.message.edit_text(
                start_text,
                reply_markup=main_menu_keyboard(lang),
                parse_mode='HTML'
            )

    @router.callback_query(F.data == "change_language")
    async def change_language(call: CallbackQuery):
        await call.message.edit_text(
            "🌐 <b>Tilni tanlang:</b>",
            reply_markup=language_keyboard(), parse_mode='HTML'
        )
        await call.answer()

    # ── Genre onboarding ───────────────────────────────────────────────────────
    @router.callback_query(GenreOnboarding.selecting, F.data.startswith("genre_toggle_"))
    async def genre_toggle(call: CallbackQuery, state: FSMContext):
        genre = call.data.replace("genre_toggle_", "")
        data = await state.get_data()
        selected = data.get('selected_genres', [])
        if genre in selected:
            selected.remove(genre)
        else:
            selected.append(genre)
        await state.update_data(selected_genres=selected)
        await call.message.edit_reply_markup(reply_markup=genre_select_keyboard(selected))
        await call.answer()

    @router.callback_query(GenreOnboarding.selecting, F.data == "genre_done")
    async def genre_done(call: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        selected = data.get('selected_genres', [])
        if selected:
            db.save_user_genres(call.from_user.id, selected)
        await state.clear()
        lang = get_lang(db, call.from_user.id)
        start_text = db.get_setting('start_text')
        await call.message.edit_text(start_text, parse_mode='HTML')
        await call.message.answer(
            "✅ Janrlar saqlandi! Endi men sizga mos animelarni tavsiya qila olaman 🎉",
            reply_markup=main_menu_keyboard(lang)
        )
        await call.answer()

    # ── Main menu texts ────────────────────────────────────────────────────────
    @router.message(F.text.in_({t['search'] for t in TEXTS_LIST}))
    async def menu_search(message: Message):
        if _is_off(db, message.from_user.id, admin_id): return
        if not await check_subscription(message.from_user.id, message.bot, db): return
        await message.answer("🔎 Animeni qanday izlaymiz?", reply_markup=search_keyboard())

    @router.message(F.text.in_({t['premium'] for t in TEXTS_LIST}))
    async def menu_premium(message: Message):
        if _is_off(db, message.from_user.id, admin_id): return
        if not await check_subscription(message.from_user.id, message.bot, db): return
        user = db.get_user(message.from_user.id)
        if user['status'] == 'Simple':
            await message.answer(
                "❌ Siz hali 💎 Premium + tarifiga obuna bo'lmadingiz!\n\n"
                "🔥 <b>Premium + imtiyozlari:</b>\n"
                "✅ Majburiy kanalga obuna yo'q!\n"
                "📥 Anime ulashish har doim ochiq!\n"
                "⚡ Barcha VIP anime ko'rish huquqi!\n"
                "🔔 Yangi anime qo'shilganda bildirishnoma!\n\n"
                "📅 1 oylik Premium + obunasini sotib olish:",
                reply_markup=premium_keyboard(), parse_mode='HTML'
            )
        else:
            await message.answer(
                f"🎉 Siz allaqachon 💎 <b>Premium +</b> da!\n\n"
                f"📅 Muddati: <b>{user['vip_time']}</b>",
                parse_mode='HTML'
            )

    @router.message(F.text.in_({t['profile'] for t in TEXTS_LIST}))
    async def menu_profile(message: Message):
        if _is_off(db, message.from_user.id, admin_id): return
        if not await check_subscription(message.from_user.id, message.bot, db): return
        user = db.get_user(message.from_user.id)
        ref_count = db.get_referral_count(message.from_user.id)
        bot_me = await message.bot.get_me()
        await message.answer(
            f"🧑‍💻 <b>Shaxsiy hisobingiz</b>\n\n"
            f"💰 Balans: <b>{user['balance']} UZS</b>\n"
            f"🆔 ID: <code>{user['user_id']}</code>\n"
            f"💎 Status: <b>{user['status']}</b>\n"
            f"👥 Taklif qilinganlar: <b>{ref_count} kishi</b>\n\n"
            f"🔗 Referral link:\n"
            f"<code>https://t.me/{bot_me.username}?start=ref_{user['user_id']}</code>",
            reply_markup=profile_keyboard(), parse_mode='HTML'
        )

    @router.message(F.text.in_({t['watchlist'] for t in TEXTS_LIST}))
    async def menu_watchlist(message: Message):
        if _is_off(db, message.from_user.id, admin_id): return
        if not await check_subscription(message.from_user.id, message.bot, db): return
        wl = db.get_user_watchlist(message.from_user.id)
        if not wl:
            await message.answer("📭 Kuzatuv ro'yxatingiz bo'sh!\n\n"
                                  "Anime sahifasidagi 🔔 tugmani bosib qo'shing.")
            return
        kb = InlineKeyboardBuilder()
        for item in wl:
            kb.row(InlineKeyboardButton(
                text=f"📺 {item['name']} ({item['episode']} qism)",
                callback_data=f"anime_{item['anime_id']}"
            ))
        await message.answer("📌 <b>Kuzatuv ro'yxatingiz:</b>",
                              reply_markup=kb.as_markup(), parse_mode='HTML')

    @router.message(F.text.in_({t['history'] for t in TEXTS_LIST}))
    async def menu_history(message: Message):
        if _is_off(db, message.from_user.id, admin_id): return
        history = db.get_user_history(message.from_user.id)
        if not history:
            await message.answer("📭 Ko'rish tarixi bo'sh!")
            return
        kb = InlineKeyboardBuilder()
        for item in history:
            kb.row(InlineKeyboardButton(
                text=f"📺 {item['name']} — {item['episode_number']}/{item['episode']} qism",
                callback_data=f"resume_{item['anime_id']}_{item['episode_number']}"
            ))
        await message.answer("🕓 <b>Ko'rish tarixi:</b>",
                              reply_markup=kb.as_markup(), parse_mode='HTML')

    @router.message(F.text.in_({t['top'] for t in TEXTS_LIST}))
    async def menu_top(message: Message):
        if _is_off(db, message.from_user.id, admin_id): return
        if not await check_subscription(message.from_user.id, message.bot, db): return
        top = db.get_top_anime(10)
        if not top:
            await message.answer("Hozircha top anime yo'q!")
            return
        text = "🏆 <b>Top 10 Anime:</b>\n\n"
        for i, anime in enumerate(top, 1):
            vip = " 💎" if anime.get('is_vip') else ""
            text += f"{i}. <b>{anime['name']}</b>{vip} — ⭐{anime['rating']} | 👁{anime['views']}\n"
        kb = InlineKeyboardBuilder()
        for anime in top:
            kb.row(InlineKeyboardButton(
                text=f"📺 {anime['name']}",
                callback_data=f"anime_{anime['id']}"
            ))
        await message.answer(text, reply_markup=kb.as_markup(), parse_mode='HTML')

    @router.message(F.text.in_({t['contact'] for t in TEXTS_LIST}))
    async def menu_contact(message: Message, state: FSMContext):
        if _is_off(db, message.from_user.id, admin_id): return
        await state.set_state(ContactAdminState.message)
        await message.answer("Adminga yubormoqchi bo'lgan xabaringizni kiriting:",
                              reply_markup=back_button())

    # ── Resume watching ────────────────────────────────────────────────────────
    @router.callback_query(F.data.startswith("resume_"))
    async def resume_watching(call: CallbackQuery):
        parts = call.data.split("_")
        anime_id, ep_num = int(parts[1]), int(parts[2])
        await _send_episode(call.message, db, anime_id, ep_num, call.from_user.id)
        await call.answer()

    # ── Contact admin FSM ──────────────────────────────────────────────────────
    @router.message(ContactAdminState.message)
    async def handle_admin_message(message: Message, state: FSMContext):
        user_id = message.from_user.id
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✍️ Javob berish", callback_data=f"reply_{user_id}"))
        await message.bot.send_message(
            chat_id=admin_id,
            text=f"📩 Yangi xabar:\n\n👤 ID: {user_id}\n💬 Xabar: {message.text}",
            reply_markup=kb.as_markup()
        )
        await state.clear()
        await message.answer("✅ Xabaringiz adminga yuborildi!", reply_markup=ask_question_keyboard())

    @router.callback_query(F.data == "ask_question")
    async def ask_question(call: CallbackQuery, state: FSMContext):
        await state.set_state(ContactAdminState.message)
        await call.message.answer("Adminga yubormoqchi bo'lgan xabaringizni kiriting:")
        await call.answer()

    @router.callback_query(F.data.startswith("reply_"))
    async def reply_to_user(call: CallbackQuery, state: FSMContext):
        target_id = int(call.data.split("_")[1])
        await state.update_data(reply_user_id=target_id)
        await state.set_state(ReplyUserState.message)
        await call.message.answer("✍️ Foydalanuvchiga javob yozing:")
        await call.answer()

    @router.message(ReplyUserState.message)
    async def handle_reply(message: Message, state: FSMContext):
        data = await state.get_data()
        target_id = data['reply_user_id']
        try:
            await message.bot.send_message(
                chat_id=target_id,
                text=f"📩 Admin javobi:\n\n{message.text}",
                reply_markup=ask_question_keyboard()
            )
            await message.answer("✅ Javob yuborildi!")
        except Exception as e:
            await message.answer(f"❌ Xato: {e}")
        await state.clear()

    # ── Search callbacks ───────────────────────────────────────────────────────
    @router.callback_query(F.data == "search_name")
    async def search_by_name_cb(call: CallbackQuery, state: FSMContext):
        await state.set_state(SearchStates.search_name)
        await call.message.edit_text(
            "🔎 Anime nomini kiriting:\n\n📝 Namuna: <code>Naruto Shippuden</code>",
            reply_markup=back_button(), parse_mode='HTML'
        )
        await call.answer()

    @router.message(SearchStates.search_name)
    async def handle_search_name(message: Message, state: FSMContext):
        await state.clear()
        results = db.search_anime_by_name(message.text)
        await _send_anime_list(message, db, results)

    @router.callback_query(F.data == "search_code")
    async def search_by_code_cb(call: CallbackQuery, state: FSMContext):
        await state.set_state(SearchStates.search_code)
        await call.message.edit_text(
            "🔎 Anime kodini kiriting:\n\n📝 Namuna: <code>99</code>",
            reply_markup=back_button(), parse_mode='HTML'
        )
        await call.answer()

    @router.message(SearchStates.search_code)
    async def handle_search_code(message: Message, state: FSMContext):
        await state.clear()
        try:
            anime_id = int(message.text)
            anime = db.search_anime_by_id(anime_id)
            if anime:
                await _send_anime_card(message, db, anime)
            else:
                await message.answer("❌ Anime topilmadi!", reply_markup=back_button())
        except ValueError:
            await message.answer("⚠️ Faqat raqam kiriting!", reply_markup=back_button())

    @router.callback_query(F.data == "search_genre")
    async def search_by_genre_cb(call: CallbackQuery, state: FSMContext):
        await state.set_state(SearchStates.search_genre)
        await call.message.edit_text(
            "🔎 Anime janrini kiriting:\n\n📌 Masalan: Action, Comedy, Drama...",
            reply_markup=back_button()
        )
        await call.answer()

    @router.message(SearchStates.search_genre)
    async def handle_search_genre(message: Message, state: FSMContext):
        await state.clear()
        results = db.search_anime_by_genre(message.text)
        await _send_anime_list(message, db, results)

    # ── Anime detail / show ────────────────────────────────────────────────────
    @router.callback_query(F.data.startswith("anime_"))
    async def show_anime_details(call: CallbackQuery):
        try:
            anime_id = int(call.data.split('_')[1])
            anime = db.search_anime_by_id(anime_id)
            if anime:
                await _send_anime_card(call.message, db, anime, call.from_user.id)
        except (ValueError, IndexError):
            await call.answer("Xatolik yuz berdi!", show_alert=True)
        await call.answer()

    # ── Watchlist toggle ───────────────────────────────────────────────────────
    @router.callback_query(F.data.startswith("watchlist_toggle_"))
    async def watchlist_toggle(call: CallbackQuery):
        anime_id = int(call.data.split("_")[-1])
        user_id = call.from_user.id
        if db.is_in_watchlist(user_id, anime_id):
            db.remove_from_watchlist(user_id, anime_id)
            await call.answer("🔕 Kuzatuvdan olib tashlandi")
        else:
            db.add_to_watchlist(user_id, anime_id)
            await call.answer("🔔 Kuzatuvga qo'shildi! Yangi qism qo'shilganda xabar olasiz")
        # Tugmani yangilash
        anime = db.search_anime_by_id(anime_id)
        if anime:
            bot_me = await call.bot.get_me()
            in_wl = db.is_in_watchlist(user_id, anime_id)
            try:
                await call.message.edit_reply_markup(
                    reply_markup=anime_detail_keyboard(bot_me.username, anime_id, in_wl)
                )
            except Exception:
                pass

    # ── Rating ─────────────────────────────────────────────────────────────────
    @router.callback_query(F.data.startswith("rate_anime_"))
    async def rate_anime(call: CallbackQuery):
        anime_id = int(call.data.split("_")[-1])
        existing = db.get_user_rating(anime_id, call.from_user.id)
        text = (f"⭐ Hozirgi bahoyingiz: {existing['rating']}/10\n\n"
                if existing else "") + "Yangi baho bering:"
        await call.message.answer(text, reply_markup=rating_keyboard(anime_id))
        await call.answer()

    @router.callback_query(F.data.startswith("give_rating_"))
    async def give_rating(call: CallbackQuery, state: FSMContext):
        parts = call.data.split("_")
        anime_id, rating = int(parts[2]), int(parts[3])
        await state.update_data(rating_anime_id=anime_id, rating_value=rating)
        await state.set_state(RatingState.review)
        await call.message.edit_text(
            f"✅ Baho: {rating}/10 ⭐\n\nSharh yozmoqchimisiz?",
            reply_markup=review_ask_keyboard(anime_id)
        )
        await call.answer()

    @router.callback_query(F.data.startswith("write_review_"))
    async def write_review_cb(call: CallbackQuery, state: FSMContext):
        await call.message.edit_text("✍️ Sharhingizni yozing:")
        await call.answer()

    @router.message(RatingState.review)
    async def handle_review(message: Message, state: FSMContext):
        data = await state.get_data()
        anime_id = data['rating_anime_id']
        rating = data['rating_value']
        db.add_rating(anime_id, message.from_user.id, rating, message.text)
        await state.clear()
        anime = db.search_anime_by_id(anime_id)
        await message.answer(
            f"✅ Rahmat! Bahoyingiz va sharhingiz saqlandi!\n"
            f"⭐ {anime['name']} yangi reytingi: {anime['rating']}/10"
        )

    @router.callback_query(F.data.startswith("reviews_"))
    async def show_reviews(call: CallbackQuery):
        anime_id = int(call.data.split("_")[-1])
        reviews = db.get_anime_reviews(anime_id)
        anime = db.search_anime_by_id(anime_id)
        if not reviews:
            await call.answer("Bu anime uchun hali sharh yo'q!", show_alert=True)
            return
        text = f"💬 <b>{anime['name']} — Sharhlar:</b>\n\n"
        for r in reviews:
            text += f"👤 <b>{r['first_name']}</b> — ⭐{r['rating']}/10\n"
            text += f"<i>{r['review']}</i>\n\n"
        await call.message.answer(text, parse_mode='HTML')
        await call.answer()

    # ── Episode navigation ─────────────────────────────────────────────────────
    @router.callback_query(F.data.startswith("ep_"))
    async def episode_nav(call: CallbackQuery):
        parts = call.data.split("_")
        anime_id, ep_num = int(parts[1]), int(parts[2])
        await _send_episode(call.message, db, anime_id, ep_num, call.from_user.id)
        await call.answer()

    # ── Inline query (istalgan chatda qidirish) ────────────────────────────────
    @router.inline_query()
    async def inline_search(query: InlineQuery):
        search_text = query.query.strip()
        if not search_text:
            results_list = db.get_top_anime(10)
        else:
            results_list = db.search_anime_by_name(search_text)[:10]

        bot_me = await query.bot.get_me()
        results = []
        for anime in results_list:
            caption = anime_caption_html(anime)
            kb = inline_watch_keyboard(bot_me.username, anime['id'])
            results.append(
                InlineQueryResultPhoto(
                    id=str(anime['id']),
                    photo_url=anime['image'],
                    thumbnail_url=anime['image'],
                    title=anime['name'],
                    description=f"⭐{anime['rating']} | {anime['genre']} | {anime['episode']} qism",
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=kb
                )
            )
        await query.answer(results, cache_time=10)

    # ── Premium callbacks ──────────────────────────────────────────────────────
    @router.callback_query(F.data == "buy_premium")
    async def buy_premium(call: CallbackQuery):
        user = db.get_user(call.from_user.id)
        if user['balance'] >= 5000:
            vip_time = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
            db.update_user_balance(call.from_user.id, -5000)
            db.set_user_vip(call.from_user.id, vip_time)
            await call.message.edit_text(
                f"✅ Premium + faollashtirildi! 🏆\n\n📅 Muddat: <b>{vip_time}</b>",
                parse_mode='HTML'
            )
        else:
            await call.message.edit_text(
                "⚠️ Balansingizda yetarlicha mablag' yo'q!\n\n"
                "➕ Pul kiritish uchun profilingizga o'ting."
            )
        await call.answer()

    @router.callback_query(F.data == "add_money")
    async def add_money(call: CallbackQuery):
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="✅ To'lov qildim", callback_data="payment_done"),
            InlineKeyboardButton(text="🔙 Ortga",         callback_data="back_main")
        )
        await call.message.edit_text(
            "💳 <b>Botga pul kiritish</b>\n\n"
            "📌 Quyidagi karta raqamiga pul tashlang va chekni yuboring.\n\n"
            "💳 Karta raqami:\n<code>12345678</code>\n"
            "👤 Karta egasi: Otajonov O.",
            reply_markup=kb.as_markup(), parse_mode='HTML'
        )
        await call.answer()

    @router.callback_query(F.data == "referral_link")
    async def referral_link(call: CallbackQuery):
        bot_me = await call.bot.get_me()
        user_id = call.from_user.id
        ref_count = db.get_referral_count(user_id)
        bonus = db.get_setting('referral_bonus') or '100'
        await call.message.answer(
            f"🔗 <b>Sizning referral linkiniz:</b>\n"
            f"<code>https://t.me/{bot_me.username}?start=ref_{user_id}</code>\n\n"
            f"👥 Taklif qilganlar: <b>{ref_count} kishi</b>\n"
            f"💰 Har bir taklif uchun: <b>{bonus} UZS</b> bonus\n\n"
            f"Linkni do'stlaringizga ulashing!",
            parse_mode='HTML'
        )
        await call.answer()

    # ── Payment FSM ────────────────────────────────────────────────────────────
    @router.callback_query(F.data == "payment_done")
    async def payment_done(call: CallbackQuery, state: FSMContext):
        await state.set_state(PaymentStates.amount)
        await call.message.edit_text(
            "💰 Qancha miqdorda to'lov qilganingizni kiriting:",
            reply_markup=back_button()
        )
        await call.answer()

    @router.message(PaymentStates.amount)
    async def handle_payment_amount(message: Message, state: FSMContext):
        try:
            amount = int(message.text)
            await state.update_data(payment_amount=amount)
            await state.set_state(PaymentStates.photo)
            await message.answer("📸 To'lov chekini rasm ko'rinishida yuboring:", reply_markup=back_button())
        except ValueError:
            await message.answer("⚠️ Faqat raqam kiriting:", reply_markup=back_button())

    @router.message(PaymentStates.photo, F.photo)
    async def handle_payment_photo(message: Message, state: FSMContext):
        data = await state.get_data()
        amount = data['payment_amount']
        photo = message.photo[-1].file_id
        user_id = message.from_user.id
        payment_id = db.add_payment(user_id, amount, photo)
        await state.clear()
        await message.answer("✅ To'lov arizasi adminga yuborildi!")
        await message.bot.send_photo(
            chat_id=admin_id, photo=photo,
            caption=(f"👤 User: {user_id}\n💰 Summa: {amount} UZS\n✅ Tasdiqlaysizmi?"),
            reply_markup=payment_confirmation_keyboard(payment_id)
        )

    @router.message(PaymentStates.photo)
    async def payment_photo_wrong(message: Message):
        await message.answer("⚠️ Faqat rasm yuboring:", reply_markup=back_button())

    @router.callback_query(F.data.startswith("confirm_payment_"))
    async def confirm_payment(call: CallbackQuery):
        payment_id = int(call.data.split('_')[-1])
        conn = db.get_connection(); cursor = conn.cursor()
        try:
            cursor.execute('SELECT user_id,amount FROM payments WHERE id=?', (payment_id,))
            payment = cursor.fetchone()
            if payment:
                user_id, amount = payment
                cursor.execute('UPDATE payments SET status=? WHERE id=?', ('confirmed', payment_id))
                cursor.execute('UPDATE users SET balance=balance+? WHERE user_id=?', (amount, user_id))
                conn.commit()
                await call.bot.send_message(chat_id=user_id,
                    text=f"✅ To'lovingiz tasdiqlandi! Balansingiz {amount} UZS ga oshirildi.")
                await call.answer("✅ Tasdiqlandi!")
        except Exception as e:
            await call.answer(f"Xato: {e}", show_alert=True)
        finally:
            conn.close()

    @router.callback_query(F.data.startswith("cancel_payment_"))
    async def cancel_payment(call: CallbackQuery):
        payment_id = int(call.data.split('_')[-1])
        db.update_payment_status(payment_id, 'cancelled')
        await call.answer("❌ Bekor qilindi")

    # ── Subscription check ─────────────────────────────────────────────────────
    @router.callback_query(F.data == "check_subscription")
    async def check_sub_cb(call: CallbackQuery):
        if await check_subscription(call.from_user.id, call.bot, db):
            lang = get_lang(db, call.from_user.id)
            start_text = db.get_setting('start_text')
            await call.message.edit_text(start_text, reply_markup=main_menu_keyboard(lang), parse_mode='HTML')
        await call.answer()

    # ── Back main ──────────────────────────────────────────────────────────────
    @router.callback_query(F.data == "back_main")
    async def back_main(call: CallbackQuery, state: FSMContext):
        await state.clear()
        lang = get_lang(db, call.from_user.id)
        start_text = db.get_setting('start_text')
        await call.message.edit_text(start_text, reply_markup=main_menu_keyboard(lang), parse_mode='HTML')
        await call.answer()


# ── Private helpers ────────────────────────────────────────────────────────────
def _is_off(db, user_id, admin_id):
    return db.get_setting('situation') == 'Off' and user_id != admin_id


async def _send_anime_card(message: Message, db: Database, anime: dict, user_id: int = None):
    bot_me = await message.bot.get_me()
    in_wl = db.is_in_watchlist(user_id, anime['id']) if user_id else False
    kb = anime_detail_keyboard(bot_me.username, anime['id'], in_wl)
    await message.answer_photo(
        photo=anime['image'],
        caption=anime_caption_html(anime),
        reply_markup=kb, parse_mode='HTML'
    )


async def _send_anime_list(message: Message, db: Database, results: list):
    if results:
        for anime in results:
            await _send_anime_card(message, db, anime)
    else:
        await message.answer(
            "❌ Anime topilmadi!\n🔍 Boshqa nom yoki janr bilan urinib ko'ring.",
            reply_markup=back_button()
        )


async def _send_anime_episodes(message: Message, db: Database, anime_id: int):
    anime = db.search_anime_by_id(anime_id)
    if not anime:
        await message.answer("Bu anime topilmadi!")
        return

    # VIP anime tekshirish
    user = db.get_user(message.from_user.id)
    if anime.get('is_vip') and user and user['status'] == 'Simple':
        await message.answer(
            "💎 Bu anime faqat <b>Premium +</b> foydalanuvchilar uchun!\n\n"
            "Premium olish uchun asosiy menyudagi 💎 tugmani bosing.",
            parse_mode='HTML'
        )
        return

    episodes = db.get_anime_episodes(anime_id)
    if not episodes:
        await message.answer("Bu animeda qismlar topilmadi!")
        return

    db.increment_views(anime_id)
    protect = db.get_setting('share') == 'true'

    # Progress tekshirish
    progress = db.get_progress(message.from_user.id, anime_id)
    start_ep = progress['episode_number'] if progress else 1

    ep = next((e for e in episodes if e['episode_number'] == start_ep), episodes[0])
    await _send_episode(message, db, anime_id, ep['episode_number'], message.from_user.id)


async def _send_episode(message: Message, db: Database, anime_id: int,
                         ep_number: int, user_id: int):
    anime = db.search_anime_by_id(anime_id)
    episodes = db.get_anime_episodes(anime_id)
    ep = next((e for e in episodes if e['episode_number'] == ep_number), None)
    if not ep:
        await message.answer("Bu qism topilmadi!")
        return

    protect = db.get_setting('share') == 'true'
    caption = (
        f"🍿 <b>{anime['name']}</b>\n"
        f"✨───────────────✨\n"
        f"🎥 <b>Qism:</b> {ep['episode_number']} / {anime['episode']}\n"
        f"✨───────────────✨\n"
        f"🎬 <b>Anime ID:</b> {anime_id}\n"
        f"📜 <b>Til:</b> {anime['language']}"
    )
    kb = episode_keyboard(anime_id, ep['episode_number'], len(episodes), protect)
    await message.answer_video(
        video=ep['file_id'],
        caption=caption, parse_mode='HTML',
        protect_content=protect,
        reply_markup=kb
    )
    db.save_progress(user_id, anime_id, ep_number)


# Ko'p tillilik uchun barcha matn variantlari
from keyboards import TEXTS
TEXTS_LIST = list(TEXTS.values())