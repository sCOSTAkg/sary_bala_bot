# Обновляем gemini_service для поддержки новых моделей 2025 года
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import PIL.Image
from dotenv import load_dotenv
from database import get_user_settings, get_chat_history, save_message, update_user_setting
from logger_config import get_logger
from services.tools_service import tools_service
import datetime
import asyncio

load_dotenv()
logger = get_logger()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiService:
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.critical("GEMINI_API_KEY not found!")
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        self.available_models = []
        
        # Автоматическое получение моделей
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    name = m.name.replace('models/', '')
                    # Фильтруем legacy, оставляем только актуальные
                    if 'gemini' in name or 'gemma' in name:
                        self.available_models.append(name)
        except Exception as e:
            logger.warning(f"Could not fetch models from API: {e}")
            # Fallback list just in case
            self.available_models = ["gemini-2.5-flash", "gemini-2.5-pro"]

        # Сортируем: сначала новые версии (3.0, 2.5), потом остальные
        self.available_models.sort(key=lambda x: x if '3' in x else 'z'+x) # Простая эвристика

    async def generate_response_stream(self, user_id: int, prompt: str, images: list = None, audio_path: str = None):
        """
        Генератор, возвращающий чанки текста.
        """
        settings = await get_user_settings(user_id)
        model_name = settings.get("selected_model", "gemini-2.5-flash")
        
        # Проверка валидности модели
        if model_name not in self.available_models:
            # Если модели нет (например, устарела 1.5), берем лучшую доступную (обычно первая в списке или 2.5-flash)
            fallback_model = "gemini-2.5-flash" if "gemini-2.5-flash" in self.available_models else self.available_models[0]
            logger.warning(f"Model {model_name} not found. Switching user {user_id} to {fallback_model}")
            model_name = fallback_model
            # Обновляем настройку пользователя
            await update_user_setting(user_id, "selected_model", model_name)
        
        logger.info(f"Stream generation for {user_id} using {model_name}.")

        generation_config = genai.GenerationConfig(
            temperature=settings["temperature"],
            max_output_tokens=settings["max_tokens"]
        )

        active_tools_names = ["search", "calculator", "weather", "rube"] if settings["use_tools"] else []
        tools = tools_service.get_tools_for_gemini(active_tools_names)
        
        streaming_enabled = settings.get("stream_response", True)
        if tools:
            streaming_enabled = False

        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=settings["system_instruction"],
                tools=tools
            )

            db_history = await get_chat_history(user_id, limit=10)
            chat_history = []
            for msg in db_history:
                if not msg["content"]:
                    continue
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

            content_parts = []
            if audio_path:
                audio_file = genai.upload_file(path=audio_path)
                while audio_file.state.name == "PROCESSING":
                    await asyncio.sleep(1)
                    audio_file = genai.get_file(audio_file.name)
                content_parts.append(audio_file)
                if not prompt:
                    prompt = "Аудио сообщение"
            
            if images:
                content_parts.extend(images)

            if prompt:
                if content_parts:
                    # Мультимодальный запрос (история текстом)
                    history_context = ""
                    if chat_history:
                        history_context = "Предыдущий диалог:\n" + "\n".join(
                            [f"{m['role']}: {m['parts'][0]}" for m in chat_history]
                        ) + "\n\n"
                    content_parts.append(history_context + prompt)
                else:
                    pass

            full_response = ""
            
            if streaming_enabled:
                if content_parts:
                    response_iterator = await model.generate_content_async(
                        content_parts,
                        generation_config=generation_config,
                        stream=True
                    )
                else:
                    chat = model.start_chat(history=chat_history)
                    response_iterator = await chat.send_message_async(
                        prompt,
                        generation_config=generation_config,
                        stream=True
                    )
                
                async for chunk in response_iterator:
                    if chunk.text:
                        full_response += chunk.text
                        yield full_response
                
            else:
                if content_parts:
                    response = await model.generate_content_async(
                        content_parts,
                        generation_config=generation_config
                    )
                else:
                    chat = model.start_chat(history=chat_history, enable_automatic_function_calling=True)
                    response = await chat.send_message_async(
                        prompt,
                        generation_config=generation_config
                    )
                
                full_response = response.text
                yield full_response

            await save_message(user_id, "user", prompt)
            await save_message(user_id, "model", full_response)

        except Exception as e:
            logger.error(f"Stream Error: {e}")
            yield f"Ошибка API: {str(e)}"

gemini_service = GeminiService()