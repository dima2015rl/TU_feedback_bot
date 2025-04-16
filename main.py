import asyncio

from bot.dao.database import delete_tables, create_tables
from bot.dao.models import create_test_data


async def on_startup():
    print("Удаление таблиц")
    await delete_tables()

    print("Создание таблиц...")
    await create_tables()

    print("Запуск инициализации тестовых данных...")
    await create_test_data()
    print("Инициализация завершена")


if __name__ == '__main__':
    asyncio.run(on_startup())
