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

class FaqCreateModel(BaseModel):
    category_id: int
    question_text: str
    answer_text: str
    file_id: str| None
    file_type: str | None

class FaqQuestionFindModel(BaseModel):
    category_id: int