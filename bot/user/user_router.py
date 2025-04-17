from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from bot.dao.dao import UserDAO
from bot.user.kbs import main_user_kb, profile_kb
from bot.user.schemas import TelegramIDModel, UserModel

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, session_with_commit: AsyncSession):
    user_id = message.from_user.id
    try:
        user_dao = UserDAO(session_with_commit)
        user_info = await user_dao.find_one_or_none(
            filters=TelegramIDModel(telegram_id=message.from_user.id)
        )
        text = ("Вы можете задать мне вопрос об обучении в ТУ им. А.А. Леонова, нажав на кнопку «Ответы на часто "
                "задаваемые вопросы», или найти нужную информацию, воспользовавшись кнопкой «Ответы на часто задаваемые вопросы». 😉")
        if not user_info:
            new_user = UserModel(
                telegram_id=message.from_user.id,
                #username=message.from_user.username,
                fio=f"{"" if message.from_user.full_name is None else message.from_user.full_name}",

            )

            await user_dao.add(new_user)
            await message.answer(text="👋🏻 Добро пожаловать!\n"+text,reply_markup=main_user_kb(user_id))
        else:
            await message.answer("👋🏻 С возвращением!\n"+text, reply_markup=main_user_kb(user_id))

    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await message.answer("Ошибка сервера. Попробуйте позже.")

@user_router.callback_query(F.data == "home")
async def page_home(call: CallbackQuery):
    await call.answer("Главная страница")
    text = ("Вы можете задать мне вопрос об обучении в ТУ им. А.А. Леонова, нажав на кнопку «Ответы на часто "
            "задаваемые вопросы», или найти нужную информацию, воспользовавшись кнопкой «Ответы на часто задаваемые вопросы». 😉")
    return await call.message.edit_text(
        f"👋🏻 С возвращением!\n {text}",
        reply_markup=main_user_kb(call.from_user.id)
    )

@user_router.callback_query(F.data == "my_profile")
async def page_about(call: CallbackQuery, session_without_commit: AsyncSession):
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
