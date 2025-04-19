from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import answer_kb
from bot.config import settings
from bot.dao.dao import UserDAO, CustomQuestionDAO
from bot.user.kbs import cancel_kb, personal_question_kb, faq_kb, yes_no_kb
from bot.user.schemas import TelegramIDModel, CreateCustomQuestionModel
from bot.user.utils import _save_question

question_router = Router()


@question_router.callback_query(F.data == "ask_question")
async def page_ask(call: CallbackQuery):
    await call.answer("Меню персонального вопроса")
    return await call.message.edit_text(
        f"👋Выберите как вы хотите задать вопрос?",
        reply_markup=personal_question_kb()
    )


@question_router.callback_query(F.data == "question_named")
async def page_question_named(call: CallbackQuery,session_without_commit: AsyncSession):
    await call.answer("Меню создания персонального вопроса")
    try:
        user_dao = UserDAO(session_without_commit)
        user = await user_dao.find_one_or_none(filters=TelegramIDModel(telegram_id=call.from_user.id))
        if user is None:
            return await call.message.edit_text(
                "⚠️ Произошла ошибка при загрузке вашего профиля. Пожалуйста, попробуйте позже.", reply_markup=faq_kb([])
            )
        if user.phone is None:
            return await call.message.edit_text(
                "⚠️ Произошла ошибка при загрузке вашего номера телефона. Измените в профиле ваши персональные данные",
                reply_markup=faq_kb([])
            )
        text = (
            f"✍️ <b>Персональный вопрос</b>\n\n"
            f"👤<b>Ваш профиль:</b>\n"
            f"✨<b>Личные данные:</b> {user.fio if user.fio else '🥷 указано 🥷'}\n"
            f"📱<b>Телефон:</b> {user.phone if user.phone else '🥷 не указан 🥷'}\n"
            f"📧<b>Email:</b> {user.email if user.email else '🥷 не указан 🥷'}\n"
            f"❗Для вопроса будут использоваться данные из вашего профиля. <b>Вы согласны?</b>"
        )
        await call.message.edit_text(
            text=text, reply_markup=yes_no_kb())
    except Exception as e:
        logger.error(f"Ошибка при загрузке профиля: {e}")
        await call.message.answer(
            "⚠️ Произошла ошибка при отправке вопроса. Пожалуйста, попробуйте позже.", reply_markup=faq_kb([])
        )


@question_router.callback_query(F.data == "confirm_yes")
async def personal_question_request(call: CallbackQuery, state: FSMContext):
    await call.answer("Меню создания персонального вопроса")
    await call.message.edit_text(
        text="✍️ <b>Персональный вопрос</b>\n\n"
             "Напишите ваш вопрос сообщением в этот чат. ", reply_markup=cancel_kb()
    )
    await state.set_state("waiting_for_personal_question")


@question_router.callback_query(F.data == "question_anon")
async def anonymous_question_request(call: CallbackQuery, state: FSMContext):
    await call.answer("Меню создания анонимного вопроса")
    await call.message.edit_text(
        text="✍️ <b>Анонимный вопрос</b>\n\n"
             "Напишите ваш вопрос сообщением в этот чат. "
             "Администратор получит его без указания ваших данных.",reply_markup=cancel_kb()
    )
    await state.set_state("waiting_for_question")


@question_router.message(StateFilter("waiting_for_personal_question"))
async def save_personal_question(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    await _save_question(message, session_with_commit, is_anonymous=False)
    await state.clear()

@question_router.message(StateFilter("waiting_for_question"))
async def save_anonymous_question(message: Message, state: FSMContext, session_with_commit: AsyncSession):
        await _save_question(message, session_with_commit, is_anonymous=True)
        await state.clear()


