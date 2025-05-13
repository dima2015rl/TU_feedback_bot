import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional, List, AsyncGenerator

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Boolean,
    Enum as SQLEnum,
    TIMESTAMP,
    Integer,
    LargeBinary, select, insert, BigInteger
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    DeclarativeBase
)

from bot.dao.database import Base, get_session_with_commit, engine


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
class QuestionStatus(str, Enum):
    PENDING = "в ожидании"
    DONE = "выполнен"
    ARCHIEVED = "архивирован" # вдруг понадобится архив


class User(Base):
    """Модель пользователя/администратора"""
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger,unique=True,index=True)
    fio: Mapped[str] = mapped_column(String(150))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # для рассылки использовать можно

    # Связи
    custom_questions: Mapped[List["CustomQuestion"]] = relationship(back_populates="user") # вопросы от пользователей


class FAQCategory(Base):
    """Категории FAQ-вопросов"""
    __tablename__ = "faq_categories"

    name: Mapped[str] = mapped_column(String(50), unique=True)

    #Связи
    questions: Mapped[List["FAQQuestion"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class FAQQuestion(Base):
    """Заранее заготовленные вопросы с ответами"""
    __tablename__ = "faq_questions"

    question_text: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)
    file_id: Mapped[Optional[str]] = mapped_column(Text)
    file_type: Mapped[Optional[str]] = mapped_column(Text)

    # Связи
    category_id: Mapped[int] = mapped_column(ForeignKey("faq_categories.id"))
    category: Mapped["FAQCategory"] = relationship(back_populates="questions")


class CustomQuestion(Base):
    """Кастомные вопросы от пользователей"""
    __tablename__ = "custom_questions"

    question_text: Mapped[str] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[QuestionStatus] = mapped_column(SQLEnum(QuestionStatus), default=QuestionStatus.PENDING)

    # Связи
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="custom_questions")


async def create_test_data():
    """Создание тестовых категорий и вопросов"""
    async with get_session_with_commit() as session:
        # Проверяем, есть ли уже данные
        result = await session.execute(select(FAQCategory))
        if result.scalars().first():
            print("Тестовые данные уже существуют")
            return

        # Создаем категории
        categories_data = [
            {"name": "Вопросы для студентов"},
            {"name": "Вопросы для абитуриентов"}
        ]

        await session.execute(insert(FAQCategory), categories_data)
        await session.commit()

        # Получаем созданные категории
        result = await session.execute(
            select(FAQCategory).where(
                FAQCategory.name.in_(["Вопросы для студентов", "Вопросы для абитуриентов"])
            )
        )
        categories = result.scalars().all()
        student_category = next(c for c in categories if c.name == "Вопросы для студентов")
        applicant_category = next(c for c in categories if c.name == "Вопросы для абитуриентов")

        # Создаем вопросы для студентов
        student_questions = [
            {
                "question_text": "Как получить студенческий билет?",
                "answer_text": "Нужно обратиться в деканат с паспортом и фото 3x4.",
                "category_id": student_category.id
            },
            {
                "question_text": "Где найти расписание?",
                "answer_text": "Расписание доступно на сайте университета в личном кабинете.",
                "category_id": student_category.id
            },
            {
                "question_text": "Как продлить книги в библиотеке?",
                "answer_text": "Книги можно продлить через личный кабинет или в библиотеке.",
                "category_id": student_category.id
            },
            {
                "question_text": "Когда начинается сессия?",
                "answer_text": "Зимняя сессия начинается 15 декабря, летняя - 15 мая.",
                "category_id": student_category.id
            },
            {
                "question_text": "Как записаться в общежитие?",
                "answer_text": "Необходимо подать заявление в студенческий отдел до 1 сентября.",
                "category_id": student_category.id
            }
        ]

        # Создаем вопросы для абитуриентов
        applicant_questions = [
            {
                "question_text": "Какие документы нужны для поступления?",
                "answer_text": "Паспорт, аттестат, 4 фото 3x4, медицинская справка.",
                "category_id": applicant_category.id
            },
            {
                "question_text": "Когда начинается приемная кампания?",
                "answer_text": "Прием документов начинается 20 июня.",
                "category_id": applicant_category.id
            },
            {
                "question_text": "Какие вступительные экзамены?",
                "answer_text": "Математика, русский язык и профильный предмет по специальности.",
                "category_id": applicant_category.id
            },
            {
                "question_text": "Есть ли подготовительные курсы?",
                "answer_text": "Да, курсы начинаются 1 октября и 1 февраля.",
                "category_id": applicant_category.id
            },
            {
                "question_text": "Какой проходной балл?",
                "answer_text": "Проходной балл зависит от специальности, в среднем 65-75 баллов.",
                "category_id": applicant_category.id
            }
        ]

        await session.execute(insert(FAQQuestion), student_questions + applicant_questions)
        await session.commit()
        print("Тестовые данные успешно созданы")

