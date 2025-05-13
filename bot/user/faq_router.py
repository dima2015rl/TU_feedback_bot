from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.dao.dao import FAQCategoryDAO, FAQQuestionDAO
from bot.user.kbs import faq_kb, question_kb, answer_kb
from bot.user.schemas import TelegramIDModel, UserModel, QuestionModel

faq_router = Router()

@faq_router.callback_query(F.data == "faq")
async def faq_catalog(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Загрузка...")
    await call.message.delete()
    categories_data = await FAQCategoryDAO(session_without_commit).find_all()
    await call.bot.send_message(chat_id=call.message.chat.id,
        text="Выберите к какой категории относится ваш вопрос:",
        reply_markup=faq_kb(categories_data)
    )

@faq_router.callback_query(F.data.startswith("faq_category_"))
async def faq_questions(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Загрузка...")
    category_id = int(call.data.split("faq_category_")[-1])
    question_data = await FAQQuestionDAO(session_without_commit).find_all(QuestionModel(category_id=category_id))
    await call.message.edit_text(
        text="Какой вопрос вас интересует?",
        reply_markup=question_kb(question_data)
    )

@faq_router.callback_query(F.data.startswith("faq_answer_"))
async def faq_questions(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Загрузка...")
    question_id = int(call.data.split("faq_answer_")[-1])
    question = await FAQQuestionDAO(session_without_commit).find_one_or_none_by_id(question_id)
    if not question:
        await call.answer("Вопрос не найден", reply_markup=answer_kb())
        return
    await call.message.delete()
    if question.file_id:
        if question.file_type == "photo":
            await call.message.answer_photo(
                photo=question.file_id,
                caption=f"❓ Вопрос: {question.question_text}\n\n💡 Ответ: {question.answer_text}",
                reply_markup=answer_kb()
            )
        elif question.file_type == "document":
            await call.message.answer_document(
                document=question.file_id,
                caption=f"❓ Вопрос: {question.question_text}\n\n💡 Ответ: {question.answer_text}",
                reply_markup=answer_kb()
            )
    else:
        await call.message.answer(
            text=f"❓ Вопрос: {question.question_text}\n\n💡 Ответ: {question.answer_text}",
            reply_markup=answer_kb()
        )