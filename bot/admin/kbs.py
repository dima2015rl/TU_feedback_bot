from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def answer_kb(question_id:int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅Ответить✅", callback_data=f"answer_question_{question_id}")
    kb.button(text="❌Удалить вопрос❌", callback_data=f"delete_question_answer_{question_id}")
    kb.adjust(1)
    return kb.as_markup()

def admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❓Ответить на вопросы❓",callback_data="list_of_questions")
    kb.button(text="ℹ️Добавить категорию для вопросовℹ️",callback_data="add_faq_categoty")
    kb.button(text="ℹ️Добавить вопрос в категориюℹ️",callback_data="add_faq_question")
    kb.button(text="Сделать массовую рассылку по пользователям", callback_data="add_faq_question")
    kb.button(text="🏠 На главную 🏠", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()