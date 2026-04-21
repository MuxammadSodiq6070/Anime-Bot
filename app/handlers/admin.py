import asyncio
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Database
from keyboards import (
    admin_panel_keyboard, anime_settings_keyboard, back_admin_button,
    channel_settings_keyboard, main_settings_keyboard,
    mandatory_channels_keyboard, send_message_keyboard,
    edit_anime_fields_keyboard, scheduled_posts_keyboard
)

router = Router()


class AddAnimeStates(StatesGroup):
    name=State(); episode=State(); country=State(); language=State()
    description=State(); genre=State(); image=State(); is_vip=State()

class AddEpisodeStates(StatesGroup):
    anime_id=State(); file=State()

class EditAnimeStates(StatesGroup):
    select=State(); field=State(); value=State()

class DeleteAnimeState(StatesGroup):
    anime_id=State()

class AddChannelStates(StatesGroup):
    channel_id=State(); channel_link=State()

class AnimeChannelSetup(StatesGroup): value=State()
class StartTextSetup(StatesGroup): value=State()
class HelpTextSetup(StatesGroup): value=State()
class AdsTextSetup(StatesGroup): value=State()
class BroadcastStates(StatesGroup): message=State()
class ForwardStates(StatesGroup): message=State()
class UserMessageStates(StatesGroup): user_id=State(); message=State()

class SchedulePostStates(StatesGroup):
    anime_id=State(); datetime_str=State()


def register_admin_handlers(router: Router, db: Database, admin_id: int):

    def is_admin(uid): return uid == admin_id

    # ── /admin ─────────────────────────────────────────────────────────────────
    @router.message(Command("admin"))
    @router.message(Command("panel"))
    async def admin_panel(message: Message):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Siz admin emassiz!"); return
        await message.answer(
            "👨‍💼 Admin panelga xush kelibsiz!",
            reply_markup=admin_panel_keyboard()
        )

    @router.callback_query(F.data == "back_admin")
    async def back_admin(call: CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.edit_text(
            "👨‍💼 Admin panelga xush kelibsiz!",
            reply_markup=admin_panel_keyboard()
        )
        await call.answer()

    @router.callback_query(F.data == "anime_settings")
    async def anime_settings(call: CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.edit_text(
            "🎥 Anime sozlamlari:", reply_markup=anime_settings_keyboard())
        await call.answer()

    # ── Kengaytirilgan statistika ──────────────────────────────────────────────
    @router.callback_query(F.data == "stats")
    async def stats(call: CallbackQuery):
        s = db.get_stats()
        top = db.get_most_viewed_anime(3)
        top_text = "\n".join([f"  {i+1}. {a['name']} — {a['views']} ko'rish"
                               for i, a in enumerate(top)])
        await call.message.edit_text(
            f"📊 <b>Bot statistikasi</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{s['total_users']}</b>\n"
            f"🆕 Bugun qo'shildi: <b>{s['today_users']}</b>\n"
            f"💎 Premium foydalanuvchilar: <b>{s['premium_users']}</b>\n\n"
            f"🎥 Jami anime: <b>{s['total_anime']}</b>\n"
            f"📀 Jami epizodlar: <b>{s['total_episodes']}</b>\n"
            f"👁 Jami ko'rishlar: <b>{s['total_views']}</b>\n\n"
            f"🏆 Eng ko'p ko'rilgan:\n{top_text}",
            reply_markup=back_admin_button(), parse_mode='HTML'
        )
        await call.answer()

    # ══════════════════════════════════════════════════════════════════════════
    # ANIME QO'SHISH
    # ══════════════════════════════════════════════════════════════════════════
    @router.callback_query(F.data == "add_anime")
    async def add_anime_start(call: CallbackQuery, state: FSMContext):
        await state.clear(); await state.set_state(AddAnimeStates.name)
        await call.message.edit_text("🎥 Anime nomini kiriting:", reply_markup=back_admin_button())
        await call.answer()

    @router.message(AddAnimeStates.name)
    async def add_anime_name(message: Message, state: FSMContext):
        await state.update_data(name=message.text); await state.set_state(AddAnimeStates.episode)
        await message.answer("💀 Anime qismlar sonini kiriting:", reply_markup=back_admin_button())

    @router.message(AddAnimeStates.episode)
    async def add_anime_episode(message: Message, state: FSMContext):
        try:
            await state.update_data(episode=int(message.text)); await state.set_state(AddAnimeStates.country)
            await message.answer("🌍 Davlatni kiriting:", reply_markup=back_admin_button())
        except ValueError:
            await message.answer("❌ Faqat son kiriting!", reply_markup=back_admin_button())

    @router.message(AddAnimeStates.country)
    async def add_anime_country(message: Message, state: FSMContext):
        await state.update_data(country=message.text); await state.set_state(AddAnimeStates.language)
        await message.answer("🔦 Tilni kiriting:", reply_markup=back_admin_button())

    @router.message(AddAnimeStates.language)
    async def add_anime_language(message: Message, state: FSMContext):
        await state.update_data(language=message.text); await state.set_state(AddAnimeStates.description)
        await message.answer("📜 Tavsifni kiriting:", reply_markup=back_admin_button())

    @router.message(AddAnimeStates.description)
    async def add_anime_description(message: Message, state: FSMContext):
        await state.update_data(description=message.text); await state.set_state(AddAnimeStates.genre)
        await message.answer("🎭 Janrni kiriting:", reply_markup=back_admin_button())

    @router.message(AddAnimeStates.genre)
    async def add_anime_genre(message: Message, state: FSMContext):
        await state.update_data(genre=message.text); await state.set_state(AddAnimeStates.image)
        await message.answer("🖼 Rasmni yuboring:", reply_markup=back_admin_button())

    @router.message(AddAnimeStates.image, F.photo)
    async def add_anime_image(message: Message, state: FSMContext):
        await state.update_data(image=message.photo[-1].file_id)
        await state.set_state(AddAnimeStates.is_vip)
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="✅ Ha (VIP only)", callback_data="anime_vip_yes"),
            InlineKeyboardButton(text="❌ Yo'q (Hammaga)", callback_data="anime_vip_no")
        )
        await message.answer("💎 Bu anime VIP only bo'ladimi?", reply_markup=kb.as_markup())

    @router.callback_query(AddAnimeStates.is_vip, F.data.in_({"anime_vip_yes", "anime_vip_no"}))
    async def add_anime_vip(call: CallbackQuery, state: FSMContext):
        is_vip = 1 if call.data == "anime_vip_yes" else 0
        data = await state.get_data()
        try:
            anime_id = db.add_anime(
                data['name'], data['episode'], data['country'], data['language'],
                data['image'], data['description'], data['genre'], is_vip
            )
            await state.clear()
            vip_text = " 💎 VIP" if is_vip else ""
            await call.message.edit_text(
                f"✅ Anime{vip_text} muvaffaqiyatli qo'shildi!\n\n🄚 Anime kodi: <code>{anime_id}</code>",
                parse_mode='HTML', reply_markup=back_admin_button()
            )
            # Watchlist subscribers'ga xabar (agar bunday anime yangi bo'lsa)
        except Exception as e:
            await call.message.edit_text(f"❌ Xatolik: {e}", reply_markup=back_admin_button())
        await call.answer()

    @router.message(AddAnimeStates.image)
    async def add_anime_image_wrong(message: Message):
        await message.answer("❌ Faqat rasm yuboring!", reply_markup=back_admin_button())

    # ══════════════════════════════════════════════════════════════════════════
    # QISM QO'SHISH — yangi qism qo'shilganda kuzatuvchilarga xabar
    # ══════════════════════════════════════════════════════════════════════════
    @router.callback_query(F.data == "add_episode")
    async def add_episode_start(call: CallbackQuery, state: FSMContext):
        await state.clear(); await state.set_state(AddEpisodeStates.anime_id)
        await call.message.edit_text("🔢 Anime ID sini kiriting:", reply_markup=back_admin_button())
        await call.answer()

    @router.message(AddEpisodeStates.anime_id)
    async def add_episode_anime_id(message: Message, state: FSMContext):
        try:
            anime_id = int(message.text)
            anime = db.search_anime_by_id(anime_id)
            if anime:
                await state.update_data(anime_id=anime_id, anime_name=anime['name'])
                await state.set_state(AddEpisodeStates.file)
                await message.answer(f"🎥 {anime['name']} uchun videoni yuboring:", reply_markup=back_admin_button())
            else:
                await message.answer("❌ Anime topilmadi!", reply_markup=back_admin_button())
        except ValueError:
            await message.answer("❌ Faqat raqam kiriting!", reply_markup=back_admin_button())

    @router.message(AddEpisodeStates.file, F.video)
    async def add_episode_file(message: Message, state: FSMContext):
        data = await state.get_data()
        anime_id = data['anime_id']
        file_id = message.video.file_id
        try:
            episodes = db.get_anime_episodes(anime_id)
            ep_number = len(episodes) + 1
            db.add_episode(anime_id, ep_number, file_id)
            await message.answer(
                f"✅ {data['anime_name']} — {ep_number}-qism yuklandi!\n"
                "Keyingi videoni yuboring yoki 🔙 Ortga bosing",
                reply_markup=back_admin_button()
            )
            # Kuzatuvchilarga xabar yuborish
            asyncio.create_task(
                _notify_subscribers(message.bot, db, anime_id, ep_number, data['anime_name'])
            )
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=back_admin_button())

    @router.message(AddEpisodeStates.file)
    async def add_episode_wrong(message: Message):
        await message.answer("❌ Faqat video yuboring!", reply_markup=back_admin_button())

    # ══════════════════════════════════════════════════════════════════════════
    # ANIME TAHRIRLASH
    # ══════════════════════════════════════════════════════════════════════════
    @router.callback_query(F.data == "edit_anime")
    async def edit_anime_start(call: CallbackQuery, state: FSMContext):
        await state.clear(); await state.set_state(EditAnimeStates.select)
        await call.message.edit_text("✏️ Tahrirlamoqchi bo'lgan anime ID:", reply_markup=back_admin_button())
        await call.answer()

    @router.message(EditAnimeStates.select)
    async def edit_anime_select(message: Message, state: FSMContext):
        try:
            anime_id = int(message.text)
            anime = db.search_anime_by_id(anime_id)
            if anime:
                await state.update_data(edit_anime_id=anime_id)
                await state.set_state(EditAnimeStates.field)
                await message.answer(
                    f"✏️ <b>{anime['name']}</b>\nQaysi maydonni tahrirlaysiz?",
                    reply_markup=edit_anime_fields_keyboard(), parse_mode='HTML'
                )
            else:
                await message.answer("❌ Topilmadi!", reply_markup=back_admin_button())
        except ValueError:
            await message.answer("❌ Faqat raqam!", reply_markup=back_admin_button())

    @router.callback_query(EditAnimeStates.field, F.data.startswith("edit_field_"))
    async def edit_anime_field(call: CallbackQuery, state: FSMContext):
        field = call.data.replace("edit_field_", "")
        await state.update_data(edit_field=field)
        await state.set_state(EditAnimeStates.value)
        names = {'name':'nomi','episode':'epizodlar soni','country':'davlati',
                 'language':'tili','description':'tavsifi','genre':'janri',
                 'image':'rasmi','is_vip':'VIP holati (0 yoki 1)'}
        await call.message.edit_text(f"✏️ Yangi {names.get(field, field)}ni kiriting:", reply_markup=back_admin_button())
        await call.answer()

    @router.message(EditAnimeStates.value, F.photo)
    async def edit_value_photo(message: Message, state: FSMContext):
        data = await state.get_data()
        if data.get('edit_field') == 'image':
            db.update_anime(data['edit_anime_id'], 'image', message.photo[-1].file_id)
            await state.clear()
            await message.answer("✅ Rasm yangilandi!", reply_markup=back_admin_button())
        else:
            await message.answer("❌ Matn kiriting!", reply_markup=back_admin_button())

    @router.message(EditAnimeStates.value, F.text)
    async def edit_value_text(message: Message, state: FSMContext):
        data = await state.get_data()
        field, value = data['edit_field'], message.text
        try:
            if field in ('episode', 'is_vip'): value = int(value)
            db.update_anime(data['edit_anime_id'], field, value)
            await state.clear()
            await message.answer(f"✅ {field} yangilandi!", reply_markup=back_admin_button())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=back_admin_button())

    # ── List / delete anime ────────────────────────────────────────────────────
    @router.callback_query(F.data == "list_anime")
    async def list_anime(call: CallbackQuery):
        anime_list = db.get_all_anime()
        if not anime_list:
            await call.message.edit_text("📭 Anime yo'q!", reply_markup=back_admin_button()); await call.answer(); return
        text = "📋 <b>Anime ro'yxati:</b>\n\n"
        for a in anime_list:
            vip = " 💎" if a.get('is_vip') else ""
            text += f"🆔 {a['id']} — {a['name']}{vip} | {a['episode']} qism | ⭐{a['rating']} | 👁{a['views']}\n"
        if len(text) > 4000: text = text[:4000] + "\n..."
        await call.message.edit_text(text, reply_markup=back_admin_button(), parse_mode='HTML')
        await call.answer()

    @router.callback_query(F.data == "delete_anime")
    async def delete_anime_start(call: CallbackQuery, state: FSMContext):
        await state.set_state(DeleteAnimeState.anime_id)
        await call.message.edit_text("🗑 O'chirmoqchi bo'lgan anime ID:", reply_markup=back_admin_button())
        await call.answer()

    @router.message(DeleteAnimeState.anime_id)
    async def handle_delete_anime(message: Message, state: FSMContext):
        try:
            anime_id = int(message.text)
            anime = db.search_anime_by_id(anime_id)
            if anime:
                db.delete_anime(anime_id); await state.clear()
                await message.answer(f"✅ {anime['name']} o'chirildi!", reply_markup=back_admin_button())
            else:
                await message.answer("❌ Topilmadi!", reply_markup=back_admin_button())
        except ValueError:
            await message.answer("❌ Faqat raqam!", reply_markup=back_admin_button())

    # ══════════════════════════════════════════════════════════════════════════
    # POST TAYYORLASH + REJALASHTIRISH
    # ══════════════════════════════════════════════════════════════════════════
    @router.callback_query(F.data == "create_post")
    async def create_post(call: CallbackQuery, state: FSMContext):
        await state.set_state(SchedulePostStates.anime_id)
        await call.message.edit_text("📺 Anime ID sini kiriting:", reply_markup=back_admin_button())
        await call.answer()

    @router.message(SchedulePostStates.anime_id)
    async def schedule_post_anime_id(message: Message, state: FSMContext):
        try:
            anime_id = int(message.text)
            anime = db.search_anime_by_id(anime_id)
            if not anime:
                await message.answer("❌ Topilmadi!", reply_markup=back_admin_button()); return
            await state.update_data(post_anime_id=anime_id)

            caption = _post_caption(anime)
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text="🚀 Hozir yuborish", callback_data=f"send_post_now_{anime_id}"))
            kb.row(InlineKeyboardButton(text="📅 Rejalashtirish", callback_data=f"schedule_post_{anime_id}"))
            kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_admin"))
            await message.answer_photo(photo=anime['image'], caption=caption,
                                        parse_mode='Markdown', reply_markup=kb.as_markup())
            await state.clear()
        except ValueError:
            await message.answer("❌ Faqat raqam!", reply_markup=back_admin_button())

    @router.callback_query(F.data.startswith("send_post_now_"))
    async def send_post_now(call: CallbackQuery):
        anime_id = int(call.data.split("_")[-1])
        await _send_to_channel(call, db, anime_id)

    @router.callback_query(F.data.startswith("schedule_post_"))
    async def schedule_post_cb(call: CallbackQuery, state: FSMContext):
        anime_id = int(call.data.split("_")[-1])
        await state.update_data(post_anime_id=anime_id)
        await state.set_state(SchedulePostStates.datetime_str)
        await call.message.answer(
            "📅 Qachon yuborilsin?\n\nFormat: <code>2025-12-31 18:00</code>",
            reply_markup=back_admin_button(), parse_mode='HTML'
        )
        await call.answer()

    @router.message(SchedulePostStates.datetime_str)
    async def handle_schedule_datetime(message: Message, state: FSMContext):
        try:
            dt = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
            data = await state.get_data()
            anime_id = data['post_anime_id']
            channel = db.get_setting('anime_channel')
            db.add_scheduled_post(anime_id, channel, dt.strftime("%Y-%m-%d %H:%M"))
            await state.clear()
            await message.answer(
                f"✅ Post rejalashtirildi!\n📅 Vaqt: <b>{dt.strftime('%Y-%m-%d %H:%M')}</b>",
                reply_markup=back_admin_button(), parse_mode='HTML'
            )
        except ValueError:
            await message.answer("❌ Format xato! Misol: <code>2025-12-31 18:00</code>",
                                  reply_markup=back_admin_button(), parse_mode='HTML')

    # Rejalashtirilgan postlar ro'yxati
    @router.callback_query(F.data == "scheduled_posts")
    async def scheduled_posts(call: CallbackQuery):
        await call.message.edit_text("📅 Rejalashtirish:", reply_markup=scheduled_posts_keyboard())
        await call.answer()

    @router.callback_query(F.data == "list_scheduled")
    async def list_scheduled(call: CallbackQuery):
        posts = db.get_all_scheduled_posts()
        if not posts:
            await call.message.edit_text("📭 Rejalashtirilgan post yo'q!", reply_markup=back_admin_button())
            await call.answer(); return
        kb = InlineKeyboardBuilder()
        for p in posts:
            kb.row(InlineKeyboardButton(
                text=f"🗓 {p['scheduled_at']} — {p['name']}",
                callback_data=f"del_scheduled_{p['id']}"
            ))
        kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_admin"))
        await call.message.edit_text(
            "📋 Rejalashtirilgan postlar (o'chirish uchun bosing):",
            reply_markup=kb.as_markup()
        )
        await call.answer()

    @router.callback_query(F.data.startswith("del_scheduled_"))
    async def del_scheduled(call: CallbackQuery):
        post_id = int(call.data.split("_")[-1])
        db.delete_scheduled_post(post_id)
        await call.answer("✅ O'chirildi!")
        posts = db.get_all_scheduled_posts()
        if not posts:
            await call.message.edit_text("📭 Rejalashtirilgan post yo'q!", reply_markup=back_admin_button())
            return
        kb = InlineKeyboardBuilder()
        for p in posts:
            kb.row(InlineKeyboardButton(
                text=f"🗓 {p['scheduled_at']} — {p['name']}",
                callback_data=f"del_scheduled_{p['id']}"
            ))
        kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_admin"))
        await call.message.edit_reply_markup(reply_markup=kb.as_markup())

    @router.callback_query(F.data.startswith("send_post_"))
    async def send_post_to_channel(call: CallbackQuery):
        if "now" in call.data or "schedule" in call.data:
            return
        anime_id = int(call.data.split('_')[-1])
        await _send_to_channel(call, db, anime_id)

    # ══════════════════════════════════════════════════════════════════════════
    # KANALLAR
    # ══════════════════════════════════════════════════════════════════════════
    @router.callback_query(F.data == "channel_settings")
    async def channel_settings(call: CallbackQuery):
        await call.message.edit_text("📣 Kanallar:", reply_markup=channel_settings_keyboard()); await call.answer()

    @router.callback_query(F.data == "mandatory_subscriptions")
    async def mandatory_subscriptions(call: CallbackQuery):
        await call.message.edit_text("🔐 Majburiy obuna:", reply_markup=mandatory_channels_keyboard()); await call.answer()

    @router.callback_query(F.data == "add_channel")
    async def add_channel_start(call: CallbackQuery, state: FSMContext):
        await state.set_state(AddChannelStates.channel_id)
        await call.message.edit_text("Kanal ID (-100 qo'ymasdan):", reply_markup=back_admin_button()); await call.answer()

    @router.message(AddChannelStates.channel_id)
    async def add_channel_id(message: Message, state: FSMContext):
        await state.update_data(channel_id=message.text); await state.set_state(AddChannelStates.channel_link)
        await message.answer("Kanal havolasi (https://t.me bilan):", reply_markup=back_admin_button())

    @router.message(AddChannelStates.channel_link)
    async def add_channel_link(message: Message, state: FSMContext):
        data = await state.get_data()
        try:
            db.add_channel(data['channel_id'], message.text, 'request')
            await message.answer("✅ Kanal qo'shildi!", reply_markup=back_admin_button())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=back_admin_button())
        await state.clear()

    @router.callback_query(F.data == "list_channels")
    async def list_channels(call: CallbackQuery):
        channels = db.get_channels('request')
        if not channels:
            await call.message.edit_text("📭 Kanal yo'q!", reply_markup=back_admin_button()); await call.answer(); return
        text = "📃 Kanallar:\n\n"
        for i, ch in enumerate(channels):
            text += f"{i+1}. <a href='{ch['channel_link']}'>Kanal</a>\n"
        await call.message.edit_text(text, parse_mode='HTML', reply_markup=back_admin_button()); await call.answer()

    @router.callback_query(F.data == "delete_channel")
    async def delete_channel_menu(call: CallbackQuery):
        channels = db.get_channels('request')
        if not channels:
            await call.message.edit_text("📭 Kanal yo'q!", reply_markup=back_admin_button()); await call.answer(); return
        kb = InlineKeyboardBuilder()
        for i, ch in enumerate(channels):
            kb.row(InlineKeyboardButton(text=f"{i+1}. {ch['channel_link']}",
                                         callback_data=f"delete_channel_{ch['channel_id']}"))
        kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_admin"))
        await call.message.edit_text("🗑 O'chirish:", reply_markup=kb.as_markup()); await call.answer()

    @router.callback_query(F.data.startswith("delete_channel_"))
    async def delete_channel_confirm(call: CallbackQuery):
        channel_id = call.data.replace("delete_channel_", "")
        db.delete_channel(channel_id)
        await call.message.edit_text("✅ Kanal o'chirildi!", reply_markup=back_admin_button()); await call.answer()

    # ══════════════════════════════════════════════════════════════════════════
    # ASOSIY SOZLAMALAR
    # ══════════════════════════════════════════════════════════════════════════
    @router.callback_query(F.data == "main_settings")
    async def main_settings(call: CallbackQuery):
        await call.message.edit_text("⚙️ Asosiy sozlamalar:", reply_markup=main_settings_keyboard(db)); await call.answer()

    @router.callback_query(F.data == "toggle_share")
    async def toggle_share(call: CallbackQuery):
        s = db.get_setting('share'); new_s = 'true' if s == 'false' else 'false'
        db.update_setting('share', new_s)
        await call.message.edit_text(
            f"✅ Uzatish {'yoqildi' if new_s=='true' else 'o_chirildi'}!",
            reply_markup=main_settings_keyboard(db)); await call.answer()

    @router.callback_query(F.data == "bot_situation_setup")
    async def bot_situation_setup(call: CallbackQuery):
        sit = db.get_setting('situation')
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(
            text="O'chirish ❌" if sit=='On' else "Yoqish ✅",
            callback_data="toggle_bot_situation"))
        kb.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="back_admin"))
        await call.message.edit_text(
            f"🤖 Bot holati: {'Yoqilgan ✅' if sit=='On' else 'O_chirilgan ❌'}",
            reply_markup=kb.as_markup()); await call.answer()

    @router.callback_query(F.data == "toggle_bot_situation")
    async def toggle_bot_situation(call: CallbackQuery):
        sit = db.get_setting('situation'); new_sit = 'Off' if sit=='On' else 'On'
        db.update_setting('situation', new_sit)
        await call.message.edit_text(
            f"✅ Bot {'o_chirildi' if new_sit=='Off' else 'yoqildi'}!",
            reply_markup=back_admin_button()); await call.answer()

    @router.callback_query(F.data == "anime_channel_setup")
    async def anime_channel_setup(call: CallbackQuery, state: FSMContext):
        await state.set_state(AnimeChannelSetup.value)
        await call.message.edit_text(
            f"🎥 Hozirgi: {db.get_setting('anime_channel')}\nYangisini kiriting:",
            reply_markup=back_admin_button()); await call.answer()

    @router.message(AnimeChannelSetup.value)
    async def handle_anime_channel(message: Message, state: FSMContext):
        db.update_setting('anime_channel', message.text); await state.clear()
        await message.answer(f"✅ Kanal o'zgartirildi!", reply_markup=back_admin_button())

    @router.callback_query(F.data == "start_text_setup")
    async def start_text_setup(call: CallbackQuery, state: FSMContext):
        await state.set_state(StartTextSetup.value)
        await call.message.edit_text(
            f"📝 Hozirgi:\n{db.get_setting('start_text')}\n\nYangisini kiriting:",
            reply_markup=back_admin_button()); await call.answer()

    @router.message(StartTextSetup.value)
    async def handle_start_text(message: Message, state: FSMContext):
        db.update_setting('start_text', message.text); await state.clear()
        await message.answer("✅ Start matni yangilandi!", reply_markup=back_admin_button())

    @router.callback_query(F.data == "help_text_setup")
    async def help_text_setup(call: CallbackQuery, state: FSMContext):
        await state.set_state(HelpTextSetup.value)
        await call.message.edit_text(
            f"ℹ️ Hozirgi:\n{db.get_setting('help_text')}\n\nYangisini kiriting:",
            reply_markup=back_admin_button()); await call.answer()

    @router.message(HelpTextSetup.value)
    async def handle_help_text(message: Message, state: FSMContext):
        db.update_setting('help_text', message.text); await state.clear()
        await message.answer("✅ Yordam matni yangilandi!", reply_markup=back_admin_button())

    @router.callback_query(F.data == "ads_text_setup")
    async def ads_text_setup(call: CallbackQuery, state: FSMContext):
        await state.set_state(AdsTextSetup.value)
        await call.message.edit_text(
            f"📢 Hozirgi:\n{db.get_setting('ads_text')}\n\nYangisini kiriting:",
            reply_markup=back_admin_button()); await call.answer()

    @router.message(AdsTextSetup.value)
    async def handle_ads_text(message: Message, state: FSMContext):
        db.update_setting('ads_text', message.text); await state.clear()
        await message.answer("✅ Reklama matni yangilandi!", reply_markup=back_admin_button())

    # ══════════════════════════════════════════════════════════════════════════
    # XABAR YUBORISH
    # ══════════════════════════════════════════════════════════════════════════
    @router.callback_query(F.data == "send_message")
    async def send_message_menu(call: CallbackQuery):
        await call.message.edit_text("✉️ Xabar yuborish:", reply_markup=send_message_keyboard()); await call.answer()

    @router.callback_query(F.data == "broadcast_message")
    async def broadcast_start(call: CallbackQuery, state: FSMContext):
        await state.set_state(BroadcastStates.message)
        await call.message.edit_text("Hamma userlarga xabar:", reply_markup=back_admin_button()); await call.answer()

    @router.message(BroadcastStates.message)
    async def handle_broadcast(message: Message, state: FSMContext):
        await state.clear()
        users = db.get_all_users(); total = len(users); sent = 0
        status_msg = await message.answer(f"Yuborish boshlandi: 0/{total}")
        for uid in users:
            try:
                await message.bot.send_message(chat_id=uid, text=message.text, parse_mode='HTML')
                sent += 1
                if sent % 10 == 0:
                    await status_msg.edit_text(f"Yuborildi: {sent}/{total}")
                await asyncio.sleep(0.05)
            except Exception: continue
        await status_msg.edit_text(f"✅ Yakunlandi: {sent}/{total}")

    @router.callback_query(F.data == "forward_message")
    async def forward_start(call: CallbackQuery, state: FSMContext):
        await state.set_state(ForwardStates.message)
        await call.message.edit_text("Forward xabarni yuboring:", reply_markup=back_admin_button()); await call.answer()

    @router.message(ForwardStates.message)
    async def handle_forward(message: Message, state: FSMContext):
        await state.clear()
        users = db.get_all_users(); total = len(users); sent = 0
        status_msg = await message.answer(f"Forward boshlandi: 0/{total}")
        for uid in users:
            try:
                await message.bot.forward_message(chat_id=uid, from_chat_id=message.chat.id,
                                                   message_id=message.message_id)
                sent += 1
                if sent % 10 == 0: await status_msg.edit_text(f"Yuborildi: {sent}/{total}")
                await asyncio.sleep(0.05)
            except Exception: continue
        await status_msg.edit_text(f"✅ Yakunlandi: {sent}/{total}")

    @router.callback_query(F.data == "user_message")
    async def user_message_start(call: CallbackQuery, state: FSMContext):
        await state.set_state(UserMessageStates.user_id)
        await call.message.edit_text("Foydalanuvchi ID:", reply_markup=back_admin_button()); await call.answer()

    @router.message(UserMessageStates.user_id)
    async def handle_user_id(message: Message, state: FSMContext):
        try:
            await state.update_data(target_user_id=int(message.text))
            await state.set_state(UserMessageStates.message)
            await message.answer("Xabarni kiriting:", reply_markup=back_admin_button())
        except ValueError:
            await message.answer("❌ Faqat raqam!", reply_markup=back_admin_button())

    @router.message(UserMessageStates.message)
    async def handle_send_to_user(message: Message, state: FSMContext):
        data = await state.get_data(); await state.clear()
        try:
            await message.bot.send_message(chat_id=data['target_user_id'], text=message.text, parse_mode='HTML')
            await message.answer("✅ Yuborildi!")
        except Exception as e:
            await message.answer(f"❌ Xato: {e}")


# ── Private helpers ────────────────────────────────────────────────────────────
def _post_caption(anime: dict) -> str:
    return (
        f"📺 *{anime['name']}* {'💎' if anime.get('is_vip') else ''}\n"
        f"┏━━━━━━━━━━━━━━━┓\n"
        f"┃ 🎞 *Qismlar:* {anime['episode']}\n"
        f"┃ 🌍 *Davlat:* {anime.get('country','')}\n"
        f"┃ 🗣 *Til:* {anime.get('language','')}\n"
        f"┃ 🔖 *Janr:* {anime['genre']}\n"
        f"┃ ⭐ *Reyting:* {anime['rating']}\n"
        f"┗━━━━━━━━━━━━━━━┛\n"
        f"📌 *Tavsif:* {anime['description']}"
    )


async def _send_to_channel(call: CallbackQuery, db: Database, anime_id: int):
    anime = db.search_anime_by_id(anime_id)
    if not anime:
        await call.answer("Anime topilmadi!", show_alert=True); return
    caption = _post_caption(anime)
    channel = db.get_setting('anime_channel')
    bot_me = await call.bot.get_me()
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔷 Tomosha qilish 🔷",
                                 url=f"https://t.me/{bot_me.username}?start={anime_id}"))
    try:
        await call.bot.send_photo(chat_id=channel, photo=anime['image'],
                                   caption=caption, parse_mode='Markdown',
                                   reply_markup=kb.as_markup())
        await call.message.edit_text("✅ Post kanalga yuborildi!", reply_markup=back_admin_button())
    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik: {e}", reply_markup=back_admin_button())
    await call.answer()


async def _notify_subscribers(bot, db: Database, anime_id: int, ep_number: int, anime_name: str):
    """Yangi qism qo'shilganda kuzatuvchilarga xabar"""
    subscribers = db.get_watchlist_subscribers(anime_id)
    bot_me = await bot.get_me()
    for user_id in subscribers:
        try:
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(
                text="▶️ Ko'rish",
                url=f"https://t.me/{bot_me.username}?start={anime_id}"
            ))
            await bot.send_message(
                chat_id=user_id,
                text=f"🔔 <b>{anime_name}</b> da yangi qism!\n\n"
                     f"📀 <b>{ep_number}-qism</b> qo'shildi!",
                reply_markup=kb.as_markup(), parse_mode='HTML'
            )
            await asyncio.sleep(0.05)
        except Exception:
            continue