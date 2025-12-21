# Обновляем main.py чтобы он просто запускался и держал connection
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import user_handlers, settings_handlers
from database import init_db

# Настройка логгера для вывода в stdout (чтобы Railway видел логи)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("main")

async def main():
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Starting bot...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(settings_handlers.router) 
    dp.include_router(user_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot is running! 🚀")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Polling error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
