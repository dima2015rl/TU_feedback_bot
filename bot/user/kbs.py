from typing import List
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from bot.config import settings
from bot.dao.models import FAQCategory, FAQQuestion


def main_user_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Мой профиль 👤", callback_data="my_profile")
    kb.button(text="ℹ️ Ответы на часто задаваемые вопросы ℹ️", callback_data="faq")
    kb.button(text="🗨️ Задать вопрос 🗨", callback_data="ask_question")#сделать
    if user_id in settings.ADMIN_IDS:
        kb.button(text="⚙️ Админ панель", callback_data="admin_panel")#сделать
    kb.adjust(1)
    return kb.as_markup()

def profile_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ Изменить личные данные", callback_data="edit_profile") #сделать
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def faq_kb(faq_categories: List[FAQCategory]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for category in faq_categories:
        kb.button(text=category.name, callback_data=f"faq_category_{category.id}")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def question_kb(faq_question: List[FAQQuestion]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for question in faq_question:
        kb.button(text=question.question_text, callback_data=f"faq_answer_{question.id}")
    kb.button(text="🔙 Назад", callback_data="faq")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()

def answer_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="faq")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()