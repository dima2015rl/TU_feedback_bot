from bot.dao.base import BaseDAO
from bot.dao.models import User, FAQCategory, FAQQuestion


class UserDAO(BaseDAO[User]):
    model = User


class FAQCategoryDAO(BaseDAO[FAQCategory]):
    model = FAQCategory


class FAQQuestionDAO(BaseDAO[FAQQuestion]):
    model = FAQQuestion