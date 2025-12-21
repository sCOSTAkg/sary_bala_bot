from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from services.gemini_service import gemini_service

# Главное меню (Reply)
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🗑 Очистить память")],
        [KeyboardButton(text="ℹ️ О боте")]
    ],
    resize_keyboard=True
)

# Меню настроек (Inline)
def get_settings_kb(settings: dict):
    model = settings.get("selected_model", "unknown")
    temp = settings.get("temperature", 0.7)
    use_tools = "✅" if settings.get("use_tools") else "❌"
    stream = "✅" if settings.get("stream_response") else "❌"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🤖 Модель: {model}", callback_data="settings_model")],
        [InlineKeyboardButton(text=f"🌡 Темп: {temp}", callback_data="settings_temp")],
        [
            InlineKeyboardButton(text=f"🛠 Tools: {use_tools}", callback_data="settings_tools"),
            InlineKeyboardButton(text=f"🌊 Stream: {stream}", callback_data="settings_stream")
        ],
        [InlineKeyboardButton(text="📝 Системная инструкция", callback_data="settings_system")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_settings")]
    ])

# Остальные функции те же...
def get_models_kb():
    models = gemini_service.available_models
    buttons = []
    for m in models:
        buttons.append([InlineKeyboardButton(text=m, callback_data=f"set_model_{m}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_temp_kb():
    temps = [0.2, 0.5, 0.7, 1.0, 1.5]
    buttons = [
        [InlineKeyboardButton(text=str(t), callback_data=f"set_temp_{t}") for t in temps],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
