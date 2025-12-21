"""
Middleware для rate limiting и валидации
"""
import time
from collections import defaultdict
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    """Ограничение частоты запросов от пользователей"""

    def __init__(self, rate_limit: int = 3, time_window: int = 60):
        """
        Args:
            rate_limit: Максимум запросов
            time_window: Временное окно в секундах
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.user_requests: Dict[int, list] = defaultdict(list)
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = time.time()

        # Очистка старых запросов
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.time_window
        ]

        # Проверка лимита
        if len(self.user_requests[user_id]) >= self.rate_limit:
            await event.answer(
                f"⏳ Превышен лимит запросов!\n"
                f"Подождите {self.time_window} секунд.\n\n"
                f"Лимит: {self.rate_limit} запросов в {self.time_window} сек."
            )
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return

        # Добавляем запрос
        self.user_requests[user_id].append(current_time)

        return await handler(event, data)


class ValidationMiddleware(BaseMiddleware):
    """Валидация входящих данных"""

    MAX_TEXT_LENGTH = 4000
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Валидация текста
        if event.text and len(event.text) > self.MAX_TEXT_LENGTH:
            await event.answer(
                f"❌ Текст слишком длинный!\n"
                f"Максимум: {self.MAX_TEXT_LENGTH} символов\n"
                f"Ваш текст: {len(event.text)} символов"
            )
            logger.warning(f"Text too long from user {event.from_user.id}: {len(event.text)}")
            return

        # Валидация фото
        if event.photo:
            photo = event.photo[-1]
            if photo.file_size > self.MAX_FILE_SIZE:
                await event.answer(
                    f"❌ Файл слишком большой!\n"
                    f"Максимум: {self.MAX_FILE_SIZE // (1024*1024)}MB"
                )
                return

        # Валидация аудио/голоса
        if event.voice or event.audio:
            audio = event.voice or event.audio
            if audio.file_size > self.MAX_FILE_SIZE:
                await event.answer(
                    f"❌ Аудио слишком большое!\n"
                    f"Максимум: {self.MAX_FILE_SIZE // (1024*1024)}MB"
                )
                return

        return await handler(event, data)
