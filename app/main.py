import asyncio
import logging
from os import getenv

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database import Database
from handlers.user import router as user_router, register_user_handlers
from handlers.admin import router as admin_router, register_admin_handlers

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_ID  = int(getenv("ADMIN_ID"))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def scheduler(bot: Bot, db: Database):
    """Har daqiqa rejalashtirilgan postlarni tekshiradi"""
    while True:
        try:
            pending = db.get_pending_posts()
            for post in pending:
                kb = InlineKeyboardBuilder()
                bot_me = await bot.get_me()
                kb.row(InlineKeyboardButton(
                    text="🔷 Tomosha qilish 🔷",
                    url=f"https://t.me/{bot_me.username}?start={post['anime_id']}"
                ))
                caption = (
                    f"📺 *{post['name']}*\n"
                    f"┏━━━━━━━━━━━━━━━┓\n"
                    f"┃ 🎞 *Qismlar:* {post['episode']}\n"
                    f"┃ 🌍 *Davlat:* {post.get('country','')}\n"
                    f"┃ 🗣 *Til:* {post.get('language','')}\n"
                    f"┃ 🔖 *Janr:* {post['genre']}\n"
                    f"┃ ⭐ *Reyting:* {post['rating']}\n"
                    f"┗━━━━━━━━━━━━━━━┛\n"
                    f"📌 *Tavsif:* {post['description']}"
                )
                try:
                    await bot.send_photo(
                        chat_id=post['channel'],
                        photo=post['image'],
                        caption=caption,
                        parse_mode='Markdown',
                        reply_markup=kb.as_markup()
                    )
                    db.mark_post_sent(post['id'])
                    logger.info(f"Scheduled post sent: {post['name']}")
                except Exception as e:
                    logger.error(f"Scheduled post error: {e}")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(60)  # Har 60 soniyada tekshiradi


async def main():
    db = Database()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    register_user_handlers(user_router, db, ADMIN_ID)
    register_admin_handlers(admin_router, db, ADMIN_ID)

    dp.include_router(admin_router)
    dp.include_router(user_router)

    logger.info("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Scheduler va polling parallel ishlaydi
    await asyncio.gather(
        dp.start_polling(bot),
        scheduler(bot, db)
    )


if __name__ == "__main__":
    asyncio.run(main())