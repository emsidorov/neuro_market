# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums.parse_mode import ParseMode
from dotenv import load_dotenv
from agent.agent import LaptopAgent
import re
import openai

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
agent = LaptopAgent(model='gpt-4o-2024-08-06')


def escape_md(text: str) -> str:
    """
    Экранирует спецсимволы для MarkdownV2, чтобы избежать ошибок форматирования.
    Список спецсимволов, которые необходимо экранировать: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    escape_chars = r'_*\[\]()~`>#+\-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


@dp.message(Command("help"))
async def handle_help(message: Message):
    help_text = (
        "Я бот, который помогает подобрать ноутбук, сравнить модели и дать подробную информацию по товарам.\n\n"
        "Вот что я умею:\n"
        "• *Подбор ноутбуков*: Просто опишите, какой ноутбук вам нужен (например, \"Ноутбук для школы\")\n"
        "• *Сравнение товаров*: Могу сравнить несколько моделей по ключевым характеристикам\n"
        "• *Информация о товарах*: Расскажу подробности о характеристиках, отзывах и ценах\n"
        "• *Подсказки и рекомендации*: Если не знаете, что выбрать, подскажу, на что обратить внимание\n\n"
        "Примеры запросов:\n"
        "• _\"Мне нужен ноутбук для школы\"_\n"
        "• _\"Сравни Apple MacBook Air и Dell XPS\"_\n"
        "• _\"Расскажи, чем отличается ноутбук с процессором i5 от i7\"_"
    )
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

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
        response = await asyncio.to_thread(agent.process_message, user_text, user_id)
    except Exception as e:
        logging.exception("Ошибка при обработке сообщения агентом")
        response = "Извини, что-то пошло не так 😔"

    print(response)
    # escaped_response = escape_md(response)
    await message.answer(response)

# Точка входа
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
