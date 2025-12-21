import logging
import os
from logging.handlers import RotatingFileHandler

# Создаем папку для логов если нет
if not os.path.exists("logs"):
    os.makedirs("logs")

# Настройка логгера
logger = logging.getLogger("sary_bala_bot")
logger.setLevel(logging.INFO)

# Форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Файловый хендлер (ротация 10МБ, хранить 5 файлов)
file_handler = RotatingFileHandler("logs/bot.log", maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(formatter)

# Консольный хендлер
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_logger():
    return logger
