from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import admin_kb
from bot.admin.schemas import QuestionUpdateModel, QuestionModel
from bot.config import settings
from bot.dao.dao import CustomQuestionDAO, UserDAO
from bot.dao.models import QuestionStatus
from bot.user.kbs import main_user_kb
from bot.user.schemas import TelegramIDModel, UserModel

admin_router = Router()


class AnswerQuestionState(StatesGroup):
    waiting_for_answer = State()

@admin_router.callback_query(F.data == "admin_panel", F.from_user.id.in_(settings.ADMIN_IDS))
async def start_admin(call: CallbackQuery):
    await call.message.edit_text(text="Доступ в админ-панель разрешен!\Выберите дейвтвие",reply_markup=admin_kb())


@admin_router.callback_query(F.data.startswith("answer_question_"))
async def answer_question(call: CallbackQuery, state: FSMContext):
    question_id = int(call.data.split("_")[-1])
    await state.update_data(question_id=question_id)

    question_text = "\n".join(call.message.text.split("\n")[1:])

    for admin_id in settings.ADMIN_IDS:
        try:
            await call.message.bot.send_message(
                chat_id=admin_id,
                text=f"В данный момент отвечают на вопрос:\n{question_text}",
            )
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")

    await call.message.delete()
    await call.message.answer(
        text=(
            "❗ Вы отвечаете на вопрос:\n\n"
            f"{question_text}\n\n"
            "Введите ваш ответ (он будет отправлен пользователю):"
        )
    )
    await state.set_state(AnswerQuestionState.waiting_for_answer)


@admin_router.message(AnswerQuestionState.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    try:
        data = await state.get_data()
        question_id = data.get("question_id")

        if not question_id:
            await state.clear()
            await message.answer("❌ Ошибка: вопрос не найден!",reply_markup=main_user_kb(message.from_user.id))

        question_dao = CustomQuestionDAO(session_with_commit)
        question = await question_dao.find_one_or_none_by_id(data_id=question_id)

        if not question:
            await state.clear()
            await message.answer("❌ Вопрос был удален или не существует!",reply_markup=main_user_kb(message.from_user.id))
            return


        if question.user_id:
            user_dao = UserDAO(session_with_commit)
            user = await user_dao.find_one_or_none_by_id(data_id=question.user_id)
            question.status = QuestionStatus.DONE

            if user and user.telegram_id:
                answer_text = (
                    "📩 <b>Ответ на ваш вопрос</b>\n\n"
                    f"❓ Ваш вопрос:\n{question.question_text}\n"
                    f"💬 Ответ:\n{message.text}"
                )

                try:
                    await message.bot.send_message(
                        chat_id=user.telegram_id,
                        text=answer_text,
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить ответ пользователю {user.telegram_id}: {e}")
                    await message.answer("⚠️ Пользователь заблокировал бота")

        await message.answer("✅ Ответ успешно отправлен!",reply_markup=main_user_kb(message.from_user.id))
    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}")
        await message.answer("❌ Произошла ошибка при обработке ответа!")
    finally:
        await state.clear()


@admin_router.callback_query(F.data.startswith("delete_question_answer_"))
async def delete_question(call: CallbackQuery, session_with_commit:AsyncSession,state: FSMContext):
    quesion_id=int(call.data[-1])
    question_dao = CustomQuestionDAO(session_with_commit)
    await question_dao.update(filters=QuestionModel(id=quesion_id),
                              values=QuestionUpdateModel(status=QuestionStatus.ARCHIEVED))
    await call.message.delete()

@admin_router.callback_query(F.data == "list_of_questions", F.from_user.id.in_(settings.ADMIN_IDS))
async def get_questions(call: CallbackQuery, session_with_commit: AsyncSession, state: FSMContext):

