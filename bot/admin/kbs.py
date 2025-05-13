from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.dao.models import FAQCategory


def answer_kb(question_id:int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅Ответить✅", callback_data=f"answer_question_{question_id}")
    kb.button(text="❌Удалить вопрос❌", callback_data=f"delete_question_answer_{question_id}")
    kb.adjust(1)
    return kb.as_markup()

def admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❓Ответить на вопросы❓",callback_data="list_of_questions")
    kb.button(text="ℹ️Работа с FAQ категориямиℹ️",callback_data="menu_faq_category")
    kb.button(text="Сделать массовую рассылку по пользователям", callback_data="send_for_all")
    kb.button(text="🏠 На главную 🏠", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def faq_kb(faq_categories: List[FAQCategory]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for category in faq_categories:
        kb.button(text=category.name, callback_data=f"menu_faq_category_{category.id}")
    kb.button(text="✅ Добавить категорию ✅", callback_data="add_faq_category")
    kb.button(text="🏠 На главную 🏠", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()

def faq_category_menu_kb(faq_category_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Добавить вопрос в эту категорию ✅",callback_data=f"q_to_faq_{faq_category_id}")
    kb.button(text="🔍Меню вопросов 🔍",callback_data=f"f_q_menu_{faq_category_id}") #сделать
    kb.button(text="🏠 На главную 🏠", callback_data="home")
    kb.button(text="❌ Удалить тему вместе с вопросами ❌",callback_data=f"d_faq_{faq_category_id}")
    kb.adjust(1)
    return kb.as_markup()

def cancel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="❌Отмена❌",callback_data="home")
    return kb.as_markup()

def accept_decline_kb(callback:str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅Да✅", callback_data=f"{callback}_y")
    kb.button(text="❌Нет❌",callback_data="home")
    kb.adjust(1)
    return kb.as_markup()