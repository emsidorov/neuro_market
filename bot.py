# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode
from dotenv import load_dotenv
from agent.agent import LaptopAgent

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
agent = LaptopAgent(model='gpt-4o-2024-08-06')

# Обработчик команды /start
@dp.message(CommandStart())
async def handle_start(message: Message):
    await message.answer("Привет! Я помогу тебе подобрать ноутбук. Просто напиши, что тебе нужно!")

# Обработчик всех остальных текстовых сообщений
@dp.message()
async def handle_text(message: Message):
    user_id = message.chat.id
    user_text = message.text

    try:
        response = await asyncio.to_thread(agent.process_message, user_text)
    except Exception as e:
        logging.exception("Ошибка при обработке сообщения агентом")
        response = "Извини, что-то пошло не так 😔"

    await message.answer(response)

# Точка входа
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
