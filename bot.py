"""
bot.py — Entry point for the Roommate Expense Bot.

Initializes the database, registers all routers, and starts polling.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import init_db
from handlers import admin_router, user_router

# ── Logging Setup ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Bot Initialization ─────────────────────────────────────────────────────────

async def main() -> None:
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database ready.")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Register routers — admin first so its callbacks have priority
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Drop pending updates before starting
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Starting bot polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
