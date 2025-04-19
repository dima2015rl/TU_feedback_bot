import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.dao.dao import UserDAO
from bot.user.kbs import profile_kb, cancel_kb, skip_kb, main_user_kb
from bot.user.schemas import TelegramIDModel, UpdateUserModel
from bot.user.utils import process_dell_text_msg

profile_router = Router()


class EditProfileData(StatesGroup):
    change_name = State()
    change_phone = State()
    change_email = State()


@profile_router.callback_query(F.data == "my_profile")
async def page_profile(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Профиль")
    try:
        user_dao = UserDAO(session_without_commit)
        user_info = await user_dao.find_one_or_none(filters=TelegramIDModel(telegram_id=call.from_user.id))
        text = (
            f"👤<b>Ваш профиль:</b>\n"
            f"✨<b>Личные данные:</b> {user_info.fio if user_info.fio else '🥷 указано 🥷'}\n"
            f"📱<b>Телефон:</b> {user_info.phone if user_info.phone else '🥷 не указан 🥷'}\n"
            f"📧<b>Email:</b> {user_info.email if user_info.email else '🥷 не указан 🥷'}"
        )
        await call.message.edit_text(
            text=text, reply_markup=profile_kb())
    except Exception as e:
        logger.error(f"Ошибка в my_profile: {e}")
        await call.answer("Ошибка сервера. Попробуйте позже.")


@profile_router.callback_query(F.data == "edit_profile")
async def start_edit_profile(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    msg = await call.message.answer(
        "✏️ Введите ваше персональные данные (Фамилию и(или) имя:",
        reply_markup=cancel_kb()
    )
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(EditProfileData.change_name)


@profile_router.message(StateFilter(EditProfileData.change_name), F.text)
async def process_set_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await process_dell_text_msg(message, state)
        await state.clear()
        await message.answer("❌ Имя слишком короткое. Введите минимум 2 символа:",reply_markup=cancel_kb())
        return
    await state.update_data(fio=name)
    await process_dell_text_msg(message, state)

    msg = await message.answer(
        "📱 Введите ваш номер телефона начиная с 9",
        reply_markup=cancel_kb()
    )
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(EditProfileData.change_phone)


@profile_router.message(StateFilter(EditProfileData.change_phone), F.text)
async def process_set_phone(message: Message, state: FSMContext):
    raw_phone = message.text.strip()

    # Удаление всех нецифровых символов
    cleaned_phone = re.sub(r'\D', '', raw_phone)

    # Нормализация номера
    if cleaned_phone.startswith('8') and len(cleaned_phone) == 11:
        formatted_phone = '+7' + cleaned_phone[1:]
    elif cleaned_phone.startswith('7') and len(cleaned_phone) == 11:
        formatted_phone = '+' + cleaned_phone
    elif cleaned_phone.startswith('9') and len(cleaned_phone) == 10:
        formatted_phone = '+7' + cleaned_phone
    else:
        await process_dell_text_msg(message, state)
        await state.clear()
        await message.answer("❌ Неверный формат номера. Пример: 89629136040",
                             reply_markup=cancel_kb())
        return



    await state.update_data(phone=formatted_phone)
    await process_dell_text_msg(message, state)

    msg = await message.answer(
        "📧 Введите ваш email или нажмите 'Пропустить':",
        reply_markup=skip_kb()
    )
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(EditProfileData.change_email)


@profile_router.message(StateFilter(EditProfileData.change_email))
async def process_set_email_and_confirm(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    email = None if message.text.lower() == "пропустить" else message.text.strip()
    await state.update_data(email=email)
    await process_dell_text_msg(message, state)
    data = await state.get_data()
    del data["last_msg_id"]
    user_dao = UserDAO(session_with_commit)
    try:
        user = await user_dao.update(filters=TelegramIDModel(telegram_id=message.from_user.id),
                                     values=UpdateUserModel(**data))
        if not user:
            raise Exception
        response = [
            "✅ Профиль успешно обновлён:",
        ]

        await message.answer(
            "\n".join(response),
            reply_markup=main_user_kb(message.from_user.id)
        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении профиля: {e}")
        await message.answer(
            "❌ Произошла ошибка при сохранении данных",
            reply_markup=main_user_kb(message.from_user.id)
        )
    finally:
        await state.clear()
