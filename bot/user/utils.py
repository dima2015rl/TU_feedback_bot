from html import escape

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import answer_kb
from bot.config import bot, settings
from bot.dao.dao import CustomQuestionDAO, UserDAO
from bot.user.kbs import faq_kb
from bot.user.schemas import TelegramIDModel, CreateCustomQuestionModel


async def process_dell_text_msg(message: Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get('last_msg_id')
    try:
        if last_msg_id:
            await bot.delete_message(chat_id=message.from_user.id, message_id=last_msg_id)
        else:
            logger.warning("Ошибка: Не удалось найти идентификатор последнего сообщения для удаления.")
        await message.delete()

    except Exception as e:
        logger.error(f"Произошла ошибка при удалении сообщения: {str(e)}")


async def _save_question(
        message: Message,
        session_with_commit: AsyncSession,
        is_anonymous: bool
):
    """Общая функция для сохранения вопросов"""
    try:
        user_dao = UserDAO(session_with_commit)

        # Получаем пользователя
        user = await user_dao.find_one_or_none(
            filters=TelegramIDModel(telegram_id=message.from_user.id))
        if not user and not is_anonymous:
            await message.answer("❌ Ошибка: профиль не найден!", reply_markup=faq_kb([]))
        question_dao = CustomQuestionDAO(session_with_commit)
        new_question = await question_dao.add(
            CreateCustomQuestionModel(
                question_text=escape(message.text),
                is_anonymous=is_anonymous,
                user_id=user.id if user else None
            )
        )
        if is_anonymous:
            admin_text = (
                "❓ <b>Новый анонимный вопрос</b>\n"
                f"📄 <b>Текст вопроса:</b>\n{escape(message.text)}"
            )
        else:

            admin_text = (
                "❓ <b>Новый персональный вопрос</b>\n"
                f"✨ <b>Личные данные пользователя:</b> {escape(user.fio) if user.fio else '—'}\n"
                f"📱 <b>Телефон:</b> <a href='tel:{user.phone}'>{user.phone}</a>\n"
                f"📧 <b>Email:</b> {escape(user.email) if user.email else '—'}\n"
                f"📄 <b>Текст вопроса:</b>\n{escape(message.text)}"
            )

        # Отправка админам
        for admin_id in settings.ADMIN_IDS:
            try:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    reply_markup=answer_kb(new_question.id),
                )
            except Exception as e:
                logger.error(f"Ошибка отправки админу {admin_id}: {e}")

        # Ответ пользователю
        await message.answer(
            "✅ Вопрос отправлен! Ответ придёт в этот чат.",
            reply_markup=faq_kb([])
        )

        return new_question

    except Exception as e:
        logger.error(f"Ошибка сохранения вопроса: {e}")
        await message.answer(
            "⚠️ Ошибка при отправке. Попробуйте позже.",
            reply_markup=faq_kb([])
        )
        return None