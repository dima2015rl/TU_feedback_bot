from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from bot.dao.database import async_session_maker, get_session_with_commit

from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from bot.dao.database import async_session_maker
import logging

logger = logging.getLogger(__name__)


class BaseDatabaseMiddleware(BaseMiddleware):
    """Базовый middleware для работы с сессиями БД."""

    def __init__(self, commit_on_exit: bool = False):
        self.commit_on_exit = commit_on_exit

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            self._inject_session(data, session)

            try:
                result = await handler(event, data)
                if self.commit_on_exit:
                    await session.commit()
                return result

            except Exception as e:
                await self._handle_error(session, e)
                raise

            finally:
                await session.close()

    def _inject_session(self, data: Dict[str, Any], session: AsyncSession) -> None:
        """Инъекция сессии в контекст."""
        raise NotImplementedError()

    async def _handle_error(self, session: AsyncSession, error: Exception) -> None:
        """Обработка ошибок."""
        logger.error(f"Database error: {error}", exc_info=True)
        await session.rollback()


class ReadOnlyDBSessionMiddleware(BaseDatabaseMiddleware):
    """Middleware для операций только для чтения (без коммита)."""

    def _inject_session(self, data: Dict[str, Any], session: AsyncSession) -> None:
        data['session_without_commit'] = session


class WriteDBSessionMiddleware(BaseDatabaseMiddleware):
    """Middleware для операций записи (с автоматическим коммитом)."""

    def __init__(self):
        super().__init__(commit_on_exit=True)

    def _inject_session(self, data: Dict[str, Any], session: AsyncSession) -> None:
        data['session_with_commit'] = session