from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🧠 Выбрать модель"),
            KeyboardButton(text="🗑 Сбросить контекст")
        ],
        [
            KeyboardButton(text="ℹ️ О боте")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Спроси меня о чем угодно..."
)

# Инлайн клавиатура для выбора модели
def get_models_kb(current_model: str):
    # current_model - это ключ, например 'flash' или 'pro'
    buttons = [
        [
            InlineKeyboardButton(text=f"{'✅ ' if current_model == 'flash' else ''}Gemini 1.5 Flash (Быстрая)", callback_data="set_model_flash"),
        ],
        [
            InlineKeyboardButton(text=f"{'✅ ' if current_model == 'pro' else ''}Gemini 1.5 Pro (Умная)", callback_data="set_model_pro"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)