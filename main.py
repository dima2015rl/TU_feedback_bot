import asyncio

from bot.admin.admin_router import admin_router
from bot.config import dp, bot
from bot.dao.database import delete_tables, create_tables
from bot.dao.database_middleware import ReadOnlyDBSessionMiddleware,WriteDBSessionMiddleware
from bot.dao.models import create_test_data
from bot.user.faq_router import faq_router
from bot.user.profile_router import profile_router
from bot.user.question_router import question_router
from bot.admin.question_router import question_router as admin_question_router
from bot.user.user_router import user_router


async def on_startup():
    print("Удаление таблиц")
    await delete_tables()

    print("Создание таблиц...")
    await create_tables()

    print("Запуск инициализации тестовых данных...")
    await create_test_data()
    print("Инициализация завершена")

async def main():
    # регистрация мидлварей
    dp.update.middleware(ReadOnlyDBSessionMiddleware())
    dp.update.middleware(WriteDBSessionMiddleware())

    # регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(faq_router)
    dp.include_router(profile_router)
    dp.include_router(question_router)
    dp.include_router(admin_router)
    dp.include_router(admin_question_router)

    # регистрация функций
    #dp.startup.register(on_startup)

    # запуск бота в режиме long polling при запуске бот очищает все обновления, которые были за его моменты бездействия
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
