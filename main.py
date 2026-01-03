import asyncio
import logging
import sys
import os
import glob
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import user_handlers, settings_handlers
from database import init_db

# Настройка логгера для вывода в stdout (стобы Railway видел логи)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("main")

def clear_temp_folder():
    """Очищает папку temp при запуске"""
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        return

    files = glob.glob(os.path.join(temp_dir, "*"))
    for f in files:
        try:
            if os.path.isfile(f):
                os.remove(f)
                logger.info(f"Deleted temp file: {f}")
        except Exception as e:
            logger.error(f"Error deleting {f}: {e}")

async def main():
    logger.info("Initializing database...")
    
    # Обработка ошибок инициализации БД
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error("Bot cannot start without database. Exiting...")
        sys.exit(1)
    
    # Очистка временных файлов
    clear_temp_folder()
    
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
