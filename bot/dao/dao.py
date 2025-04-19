from bot.dao.base import BaseDAO
from bot.dao.models import User, FAQCategory, FAQQuestion, CustomQuestion


class UserDAO(BaseDAO[User]):
    model = User


class FAQCategoryDAO(BaseDAO[FAQCategory]):
    model = FAQCategory


class FAQQuestionDAO(BaseDAO[FAQQuestion]):
    model = FAQQuestion

class CustomQuestionDAO(BaseDAO[CustomQuestion]):
    model = CustomQuestion