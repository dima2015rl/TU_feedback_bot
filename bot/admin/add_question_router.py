from html import escape

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import admin_kb, faq_kb, faq_category_menu_kb, accept_decline_kb
from bot.admin.schemas import FaqModel, FaqCreateModel
from bot.config import settings
from bot.dao.dao import FAQCategoryDAO, FAQQuestionDAO
from bot.admin.kbs import cancel_kb
from bot.user.kbs import yes_no_kb
from bot.user.utils import process_dell_text_msg

add_question_router = Router()

class AddFAQQuestion(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()
    waiting_for_file = State()


@add_question_router.callback_query(F.data.startswith("q_to_faq_"))
async def start_adding_question(call: CallbackQuery, state: FSMContext):
    faq_category_id = int(call.data.split("_")[-1])

    # Устанавливаем состояние и сохраняем ID категории
    await state.update_data(category_id=faq_category_id,last_msg_id=call.message.message_id)
    await call.message.edit_text("Введите текст вопроса:",reply_markup=cancel_kb())
    await state.set_state(AddFAQQuestion.waiting_for_question)


@add_question_router.message(AddFAQQuestion.waiting_for_question)
async def process_question_text(message: Message, state: FSMContext):
    await process_dell_text_msg(message,state)
    await state.update_data(question_text=message.text)
    await state.set_state(AddFAQQuestion.waiting_for_answer)
    msg = await message.answer("Теперь введите текст ответа на вопрос:",reply_markup=cancel_kb())
    await state.update_data(last_msg_id=msg.message_id)

@add_question_router.message(AddFAQQuestion.waiting_for_answer)
async def process_answer_text(message: Message, state: FSMContext):
    await state.update_data(answer_text=message.text)
    await process_dell_text_msg(message, state)

    skip_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    msg = await message.answer(
        "Теперь вы можете отправить файл (PDF, Word или PNG), который нужно прикрепить к вопросу, или нажмите 'Пропустить':",
        reply_markup=skip_kb
    )
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddFAQQuestion.waiting_for_file)


@add_question_router.message(AddFAQQuestion.waiting_for_file)
async def process_file_or_skip(message: Message, state: FSMContext,session_without_commit:AsyncSession):
    file_id = None
    file_type = None
    data = await state.get_data()
    category_id = data.get("category_id")
    category_dao = FAQCategoryDAO(session=session_without_commit)
    category = await category_dao.find_one_or_none_by_id(category_id)
    message_text = (f"Проверьте, все ли корректно:\n\n"
                    f"Тема : {category.name}\n"
                    f"❓ Вопрос: {data['question_text']}\n"
                    f"💡 Ответ: {data['answer_text']}\n"
                    f'<b>Если вы нажмете на "Да" то вопрос вместе с ответом сохранится!</b>\n'
                    )

    # Проверяем, не нажал ли пользователь "Пропустить"
    if message.text == "Пропустить":
        await process_dell_text_msg(message, state)
        msg = await message.answer(text=message_text,reply_markup=accept_decline_kb("add_question"))
        await state.update_data(file_type=file_type, file_id=file_id, last_msg_id=msg.message_id)
        return
    else:
        if message.document:
            file_id = message.document.file_id
            file_type = "document"
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        else:
            await message.answer("Пожалуйста, отправьте файл (PDF, Word или PNG) или нажмите 'Пропустить'.",reply_markup=cancel_kb())
            return

    await process_dell_text_msg(message, state)
    if file_type == "photo":
        msg = await message.answer_photo(file_id,caption=message_text,reply_markup=accept_decline_kb("add_question"))
        await state.update_data(file_type=file_type, file_id=file_id, last_msg_id=msg.message_id)

    elif file_type == "document":
        msg = await message.answer_document(file_id,caption=message_text,reply_markup=accept_decline_kb("add_question"))
        await state.update_data(file_type=file_type, file_id=file_id,last_msg_id=msg.message_id)

@add_question_router.callback_query(F.data == "add_question_y")
async def process_add_question_y(call: CallbackQuery, state: FSMContext,session_with_commit: AsyncSession):
   await call.answer("Сохраняю вопрос...")
   data = await state.get_data()
   await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=data["last_msg_id"])
   del data["last_msg_id"]
   faq_question_dao = FAQQuestionDAO(session_with_commit)
   await faq_question_dao.add(FaqCreateModel(**data))
   await state.clear()
   await call.message.answer(text="Вопрос успешно добавлен в базу данных!", reply_markup=admin_kb())

