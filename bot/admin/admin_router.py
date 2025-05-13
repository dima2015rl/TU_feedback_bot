import asyncio
from html import escape

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import admin_kb, faq_kb, faq_category_menu_kb, accept_decline_kb
from bot.admin.schemas import FaqModel, FaqQuestionFindModel, QuestionModel
from bot.config import settings
from bot.dao.dao import FAQCategoryDAO, FAQQuestionDAO, UserDAO
from bot.admin.kbs import cancel_kb
from bot.user.kbs import yes_no_kb

admin_router = Router()


class FaqThemeState(StatesGroup):
    set_name = State()

@admin_router.callback_query(F.data == "admin_panel", F.from_user.id.in_(settings.ADMIN_IDS))
async def start_admin(call: CallbackQuery):
    await call.message.edit_text(text="Доступ в админ-панель разрешен!\nВыберите действие",reply_markup=admin_kb())

@admin_router.callback_query(F.data == "menu_faq_category", F.from_user.id.in_(settings.ADMIN_IDS))
async def faq_list(call: CallbackQuery,session_without_commit: AsyncSession):
    faq_categories = await FAQCategoryDAO(session_without_commit).find_all()
    await call.message.edit_text(text="⚙️Работа с FAQ-категориями⚙️",reply_markup=faq_kb(faq_categories))

@admin_router.callback_query(F.data.startswith("menu_faq_category_"),F.from_user.id.in_(settings.ADMIN_IDS))
async def faq_menu(call: CallbackQuery, session_without_commit:AsyncSession):
    faq_dao = FAQCategoryDAO(session_without_commit)
    faq_id= int(call.data.split("_")[-1])
    faq_theme = await faq_dao.find_one_or_none_by_id(faq_id)
    if not faq_theme:
        await call.message.edit_text(text="❌Данная тема была удалена другим администратором",reply_markup=admin_kb())
    await call.message.edit_text(f'⚙️Работа с категорией "{faq_theme.name}"⚙️',
                                 reply_markup=faq_category_menu_kb(faq_id))

@admin_router.callback_query(F.data == "add_faq_category", F.from_user.id.in_(settings.ADMIN_IDS))
async def add_faq(call: CallbackQuery,state: FSMContext):
    await call.message.edit_text(text=f"✍️Введите название для новой категории вопросов✍️",reply_markup=cancel_kb())
    await state.set_state(FaqThemeState.set_name)

@admin_router.message(FaqThemeState.set_name, F.from_user.id.in_(settings.ADMIN_IDS))
async def add_faq_category(message: Message,state: FSMContext):
    faq_category_name = escape(message.text)
    await state.update_data(name=faq_category_name)
    await message.answer(text=f"Вы уверены, что хотите добавить тему: {faq_category_name}?",
                              reply_markup=accept_decline_kb("add_faq"))

@admin_router.callback_query(F.data == "add_faq_y", F.from_user.id.in_(settings.ADMIN_IDS))
async def add_faq_category_finally(call: CallbackQuery,session_with_commit: AsyncSession,state: FSMContext):
    data = await state.get_data()
    try:
        faq_dao = FAQCategoryDAO(session_with_commit)
        new_theme = await faq_dao.add(FaqModel(**data))

        if new_theme:
            await call.message.edit_text(
                text="✅ Новая тема успешно добавлена",
                reply_markup=admin_kb()
            )
    except IntegrityError as e:
        logger.error(f"Ошибка уникальности: {e}")
        await call.message.edit_text(
            text="❌ Тема с таким названием уже существует!",
            reply_markup=admin_kb()
        )
        await session_with_commit.rollback()

    except Exception as e:
        logger.error(f"Ошибка в добавлении темы: {e}")
        await call.message.edit_text(
            text="❌ Произошла ошибка при добавлении темы",
            reply_markup=admin_kb()
        )

    finally:
        await state.clear()

@admin_router.callback_query(F.data.startswith("d_faq_"), F.from_user.id.in_(settings.ADMIN_IDS))
async def remove_faq_theme(call: CallbackQuery,session_without_commit: AsyncSession,state: FSMContext):
    faq_dao = FAQCategoryDAO(session_without_commit)
    faq_id = int(call.data.split("_")[-1])
    faq_theme = await faq_dao.find_one_or_none_by_id(faq_id)
    if not faq_theme:
        await call.message.edit_text(text="❌Данная тема была удалена другим администратором", reply_markup=admin_kb())
    await call.message.edit_text(text=f"Вы уверены, что хотите удалить тему: {faq_theme.name}?\n"
                                      f"<b>Все вопросы, которые были в неё добавлены тоже будут удалены.</b>",
                                 reply_markup=accept_decline_kb(f"remove_theme_{faq_theme.id}"))



@admin_router.callback_query(F.data.startswith("remove_theme_"), F.from_user.id.in_(settings.ADMIN_IDS))
async def remove_faq_theme_finally(call: CallbackQuery,session_with_commit: AsyncSession):
    faq_theme_id=int(call.data.split("_")[-2])
    faq_dao = FAQCategoryDAO(session_with_commit)
    try:
        theme = await faq_dao.find_one_or_none_by_id(faq_theme_id)

        if not theme:
            await call.message.edit_text(
                text="❌ Тема не найдена!",
                reply_markup=admin_kb()
            )
            return

        await session_with_commit.delete(theme)
        await session_with_commit.commit()

        await call.message.edit_text(
            text="✅ Тема и все связанные вопросы успешно удалены!",
            reply_markup=admin_kb()
        )

    except IntegrityError as e:
        await session_with_commit.rollback()
        logger.error(f"Ошибка удаления темы {faq_theme_id}: {e}")
        await call.message.edit_text(
            text="❌ Не удалось удалить тему (возможно, есть связанные данные)",
            reply_markup=admin_kb()
        )

    except Exception as e:
        await session_with_commit.rollback()
        logger.error(f"Неожиданная ошибка при удалении темы {faq_theme_id}: {e}")
        await call.message.edit_text(
            text="❌ Произошла непредвиденная ошибка",
            reply_markup=admin_kb()
        )


@admin_router.callback_query(F.data.startswith("f_q_menu_"), F.from_user.id.in_(settings.ADMIN_IDS))
async def send_questions(call: CallbackQuery,session_without_commit: AsyncSession):
    quesions_dao = FAQQuestionDAO(session_without_commit)
    faq_id = int(call.data.split("f_q_menu_")[-1])
    questions = await quesions_dao.find_all(filters=FaqQuestionFindModel(category_id=faq_id))
    if not questions:
        await call.message.edit_text(f"❌В данной теме отсутствуют вопросы",reply_markup=admin_kb())
    await call.message.edit_text("⚙️Сейчас вам отправятся все вопросы из этой категории, пожалуйста ожидайте")
    for question in questions:
        if question.file_id:
            if question.file_type == "photo":
                await call.message.answer_photo(
                    photo=question.file_id,
                    caption=f"❓ Вопрос: {question.question_text}\n\n💡 Ответ: {question.answer_text}\n\n<b>Вы хотите удалить"
                            f" этот вопрос?</b>",
                    reply_markup=accept_decline_kb(f"dq_{question.id}")
                )
            elif question.file_type == "document":
                await call.message.answer_document(
                    document=question.file_id,
                    caption=f"❓ Вопрос: {question.question_text}\n\n💡 Ответ: {question.answer_text}\n\n<b>Вы хотите удалить"
                            f" этот вопрос?</b>",
                    reply_markup=accept_decline_kb(f"dq_{question.id}")
                )
        else:
            await call.message.answer(
                text=f"❓ Вопрос: {question.question_text}\n\n💡 Ответ: {question.answer_text}\n\n<b>Вы хотите удалить"
                            f" этот вопрос?</b>",
                reply_markup=accept_decline_kb(f"dq_{question.id}")
            )

@admin_router.callback_query(F.data.startswith("dq_"), F.from_user.id.in_(settings.ADMIN_IDS))
async def delete_question_by_id(call: CallbackQuery,session_with_commit: AsyncSession):
    quesions_dao = FAQQuestionDAO(session_with_commit)
    question_id = int(call.data.split("_")[-2])
    question = await quesions_dao.delete(filters=QuestionModel(id=question_id))
    await call.message.answer("✅Вопрос успешно удалён!✅",reply_markup=admin_kb())


class MassSendState(StatesGroup):
    waiting_for_content = State()


@admin_router.callback_query(F.data == "send_for_all", F.from_user.id.in_(settings.ADMIN_IDS))
async def start_mass_send(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        text="📨 Отправьте сообщение, фото или документ (PDF/DOCX) для рассылки:",
        reply_markup=cancel_kb()
    )
    await state.set_state(MassSendState.waiting_for_content)


async def send_chunk(bot: Bot, users_chunk: list, content: dict, semaphore: asyncio.Semaphore):
    async with semaphore:
        tasks = []
        for user in users_chunk:
            task = asyncio.create_task(send_to_user(bot, user.telegram_id, content))
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)


async def send_to_user(bot: Bot, chat_id: int, content: dict):
    try:
        if content['type'] == 'text':
            await bot.send_message(
                chat_id=chat_id,
                text=content['text'],
                parse_mode=ParseMode.HTML
            )
        elif content['type'] == 'photo':
            if content.get('caption'):
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=content['file_id'],
                    caption=content['caption'],
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_photo(chat_id=chat_id, photo=content['file_id'])
        elif content['type'] == 'document':
            if content.get('caption'):
                await bot.send_document(
                    chat_id=chat_id,
                    document=content['file_id'],
                    caption=content['caption'],
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_document(chat_id=chat_id, document=content['file_id'])
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки пользователю {chat_id}: {e}")
        return False


@admin_router.message(StateFilter(MassSendState.waiting_for_content))
async def process_mass_send(message: Message, state: FSMContext, bot: Bot, session_without_commit: AsyncSession):
    user_dao = UserDAO(session_without_commit)
    users = await user_dao.find_all()

    # Определяем тип контента
    content = {'type': 'text', 'text': message.text}

    if message.photo:
        content = {
            'type': 'photo',
            'file_id': message.photo[-1].file_id,
            'caption': message.caption
        }
    elif message.document:
        if message.document.mime_type in (
        'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
            content = {
                'type': 'document',
                'file_id': message.document.file_id,
                'caption': message.caption
            }
        else:
            await message.answer("❌ Поддерживаются только PDF и DOCX документы!")
            return

    # Статусное сообщение
    status_msg = await message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")

    # Настройки для ограничения скорости
    CHUNK_SIZE = 30  # Размер пачки пользователей
    MAX_CONCURRENT = 5  # Максимум одновременных пачек
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Разбиваем пользователей на пачки
    user_chunks = [users[i:i + CHUNK_SIZE] for i in range(0, len(users), CHUNK_SIZE)]

    success = 0
    failed = 0
    processed = 0

    for i, chunk in enumerate(user_chunks, 1):
        results = await send_chunk(bot, chunk, content, semaphore)
        chunk_success = sum(1 for r in results if r is True)
        success += chunk_success
        failed += len(chunk) - chunk_success
        processed += len(chunk)

        # Обновляем статус каждые 5 пачек
        if i % 5 == 0 or i == len(user_chunks):
            try:
                await status_msg.edit_text(
                    f"📨 Рассылка в процессе...\n\n"
                    f"• Обработано: {processed}/{len(users)}\n"
                    f"• Успешно: {success}\n"
                    f"• Не удалось: {failed}\n"
                    f"• Прогресс: {int(processed / len(users) * 100)}%"
                )
            except:
                pass

    # Финальный отчет
    await status_msg.edit_text(
        f"✅ Рассылка завершена!\n\n"
        f"• Всего пользователей: {len(users)}\n"
        f"• Успешно: {success}\n"
        f"• Не удалось: {failed}\n"
        f"• Тип контента: {content['type']}"
    )
    await state.clear()