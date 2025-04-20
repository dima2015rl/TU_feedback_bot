from pydantic import BaseModel

from bot.dao.models import QuestionStatus


class QuestionModel(BaseModel):
    id: int

class QuestionUpdateModel(BaseModel):
    status: QuestionStatus

class FaqModel(BaseModel):
    name: str

class FaqIdModel(BaseModel):
    id: int