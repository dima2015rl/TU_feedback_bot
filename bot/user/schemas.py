from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from bot.dao.models import QuestionStatus


class TelegramIDModel(BaseModel):
    telegram_id: int

    model_config = ConfigDict(from_attributes=True)


class UserModel(TelegramIDModel):
    #username: str | None
    fio: str | None

class QuestionModel(BaseModel):
    category_id: int

class CreateCustomQuestionModel(BaseModel):
    question_text: str
    is_anonymous: bool = True
    user_id: int

class UpdateUserModel(BaseModel):
    fio: str | None
    email: str | None
    phone: str
