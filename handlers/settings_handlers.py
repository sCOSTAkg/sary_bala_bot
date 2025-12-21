from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user_settings, update_user_setting
from keyboards.settings_kb import get_settings_kb, get_models_kb, get_temp_kb

router = Router()

class SettingsStates(StatesGroup):
    waiting_for_system_prompt = State()

@router.message(F.text == "⚙️ Настройки")
async def open_settings(message: Message):
    settings = await get_user_settings(message.from_user.id)
    await message.answer("🔧 Настройки бота:", reply_markup=get_settings_kb(settings))

@router.callback_query(F.data == "settings_model")
async def show_models(callback: CallbackQuery):
    await callback.message.edit_text("Выберите модель:", reply_markup=get_models_kb())

@router.callback_query(F.data.startswith("set_model_"))
async def set_model(callback: CallbackQuery):
    model = callback.data.replace("set_model_", "")
    await update_user_setting(callback.from_user.id, "selected_model", model)
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text(f"✅ Модель установлена: {model}", reply_markup=get_settings_kb(settings))

@router.callback_query(F.data == "settings_temp")
async def show_temp(callback: CallbackQuery):
    await callback.message.edit_text("Выберите креативность (температуру):", reply_markup=get_temp_kb())

@router.callback_query(F.data.startswith("set_temp_"))
async def set_temp(callback: CallbackQuery):
    temp = float(callback.data.replace("set_temp_", ""))
    await update_user_setting(callback.from_user.id, "temperature", temp)
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text(f"✅ Температура установлена: {temp}", reply_markup=get_settings_kb(settings))

@router.callback_query(F.data == "settings_tools")
async def toggle_tools(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    new_val = not settings["use_tools"]
    await update_user_setting(callback.from_user.id, "use_tools", int(new_val))
    settings["use_tools"] = new_val
    await callback.message.edit_text(
        f"Инструменты {'ВКЛ' if new_val else 'ВЫКЛ'}", 
        reply_markup=get_settings_kb(settings)
    )

@router.callback_query(F.data == "settings_stream")
async def toggle_stream(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    # По умолчанию stream_response = 1 (True), если колонки нет - вернется None
    current = settings.get("stream_response")
    new_val = 0 if current else 1
    
    await update_user_setting(callback.from_user.id, "stream_response", new_val)
    settings["stream_response"] = new_val
    
    msg = "Потоковый ответ ВКЛЮЧЕН 🌊" if new_val else "Потоковый ответ ВЫКЛЮЧЕН 🛑"
    await callback.message.edit_text(msg, reply_markup=get_settings_kb(settings))

@router.callback_query(F.data == "settings_system")
async def ask_system_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите новую системную инструкцию (роль бота):")
    await state.set_state(SettingsStates.waiting_for_system_prompt)
    await callback.answer()

@router.message(SettingsStates.waiting_for_system_prompt)
async def set_system_prompt(message: Message, state: FSMContext):
    await update_user_setting(message.from_user.id, "system_instruction", message.text)
    await message.answer("✅ Системная инструкция обновлена!")
    await state.clear()
    settings = await get_user_settings(message.from_user.id)
    await message.answer("🔧 Настройки:", reply_markup=get_settings_kb(settings))

@router.callback_query(F.data == "back_to_settings")
async def back_settings(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text("🔧 Настройки бота:", reply_markup=get_settings_kb(settings))

@router.callback_query(F.data == "close_settings")
async def close_settings(callback: CallbackQuery):
    await callback.message.delete()
