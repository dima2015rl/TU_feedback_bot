from html import escape

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import admin_kb, faq_kb, faq_category_menu_kb, accept_decline_kb
from bot.admin.schemas import FaqModel
from bot.config import settings
from bot.dao.dao import FAQCategoryDAO
from bot.admin.kbs import cancel_kb

admin_router = Router()


class FaqThemeState(StatesGroup):
    set_name = State()

@admin_router.callback_query(F.data == "admin_panel", F.from_user.id.in_(settings.ADMIN_IDS))
async def start_admin(call: CallbackQuery):
    await call.message.edit_text(text="Доступ в админ-панель разрешен!\nВыберите дейвтвие",reply_markup=admin_kb())

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
        await session_with_commit.rollback()  # Важно откатить транзакцию

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

