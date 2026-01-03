import io
import os
import PIL.Image
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, ContentType
from services.gemini_service import gemini_service
from keyboards.settings_kb import main_kb
from database import clear_history, get_user_settings
from logger_config import get_logger

router = Router()
logger = get_logger()

# Создаем папку для временных файлов
if not os.path.exists("temp"):
    os.makedirs("temp")

@router.message(CommandStart())
async def command_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Я Sary Bala - мультимодальный бот.\n\n"
        "Отправляй:\n"
        "📷 Фото\n"
        "🎙 Голосовые\n"
        "📝 Текст\n"
        "🌊 Поддерживаю стриминг (эффект печати)\n\n"
        "Нажми /settings или кнопку ниже для настроек.",
        reply_markup=main_kb
    )

@router.message(F.text == "🗑 Очистить память")
async def clear_mem(message: Message):
    await clear_history(message.from_user.id)
    await message.answer("История диалога очищена! 🧠✨")

@router.message(F.text == "ℹ️ О боте")
async def about(message: Message):
    settings = await get_user_settings(message.from_user.id)
    text = (
        f"🤖 **Sary Bala Bot v2.6**\n\n"
        f"Модель: `{settings['selected_model']}`\n"
        f"Температура: `{settings['temperature']}`\n"
        f"Стриминг: {'Вкл 🌊' if settings.get('stream_response') else 'Выкл 🛑'}\n"
        f"Инструменты: {'Вкл 🛠' if settings['use_tools'] else 'Выкл'}\n"
    )
    try:
        await message.answer(text, parse_mode="Markdown")
    except Exception:
         await message.answer(text, parse_mode=None)

@router.message(F.content_type.in_({'voice', 'audio'}))
async def voice_handler(message: Message, bot: Bot):
    # Логика та же, но используем stream handler
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    file_id = message.voice.file_id if message.voice else message.audio.file_id
    file = await bot.get_file(file_id)
    file_ext = file.file_path.split('.')[-1]
    local_filename = f"temp/{file_id}.{file_ext}"
    
    await bot.download_file(file.file_path, local_filename)
    
    try:
        await handle_response_stream(message, prompt=message.caption or "", audio_path=local_filename)
    except Exception as e:
        await message.answer("Ошибка обработки аудио 😞")
        logger.error(f"Voice error: {e}")
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)

@router.message()
async def chat_handler(message: Message, bot: Bot):
    if not message.text and not message.photo and not message.caption:
        return

    images = []
    prompt = message.text or (message.caption if message.caption else "")

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_stream = io.BytesIO()
        await bot.download_file(file_info.file_path, destination=file_stream)
        file_stream.seek(0)
        try:
            img = PIL.Image.open(file_stream)
            images.append(img)
            if not prompt: prompt = "Опиши это."
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            await message.answer("Ошибка картинки 😞")
            return

    await handle_response_stream(message, prompt, images)

async def handle_response_stream(message: Message, prompt: str, images: list = None, audio_path: str = None):
    """Общий обработчик с поддержкой стриминга и защитой от FloodWait"""
    
    answer_msg = await message.answer("⏳ Думаю...")
    
    last_text = ""
    last_update_time = 0
    chunk_text = ""
    import time
    
    try:
        async for chunk_text in gemini_service.generate_response_stream(
            message.from_user.id, prompt, images, audio_path
        ):
            # Telegram разрешает редактировать сообщение не чаще чем раз в ~1-2 сек (для разных чатов по-разному, но безопасно раз в 1.5с)
            current_time = time.time()
            
            # Обновляем, если прошло > 1.0 сек ИЛИ текст изменился значительно (>50 симв)
            if (current_time - last_update_time > 1.0) or (len(chunk_text) - len(last_text) > 100):
                try:
                    await answer_msg.edit_text(chunk_text + " ▌") 
                    last_text = chunk_text
                    last_update_time = current_time
                except Exception:
                    pass 
            
        # Финальное обновление
        if last_text != chunk_text:
            try:
                await answer_msg.edit_text(chunk_text, parse_mode="Markdown")
            except Exception:
                # Если Markdown сломался, отправляем как есть
                await answer_msg.edit_text(chunk_text, parse_mode=None)
        else:
            try:
                await answer_msg.edit_text(chunk_text, parse_mode="Markdown")
            except Exception:
                await answer_msg.edit_text(chunk_text, parse_mode=None)
            
    except Exception as e:
        logger.error(f"Handler error: {e}")
        await answer_msg.edit_text(f"Произошла ошибка: {e}")
