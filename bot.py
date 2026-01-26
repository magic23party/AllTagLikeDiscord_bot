"""
Telegram бот для тега всех участников группы (Pyrogram версия)
Получает список участников напрямую через API — не нужен Group Privacy!

Команды:
  /all или @all - упомянуть всех участников группы
  /help - показать справку
"""

import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMembersFilter, ChatType

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем данные из переменных окружения
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Проверка наличия всех переменных
if not all([API_ID, API_HASH, BOT_TOKEN]):
    logger.error("❌ Не заданы переменные окружения!")
    logger.error("Нужны: API_ID, API_HASH, BOT_TOKEN")
    exit(1)

# Создаём клиент
app = Client(
    "tag_all_bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    """Обработчик команды /start"""
    await message.reply_text(
        "👋 Привет! Я бот для упоминания всех участников группы.\n\n"
        "📝 Добавь меня в группу и дай права администратора.\n\n"
        "🔹 Используй /all или напиши @all чтобы упомянуть всех.\n"
        "🔹 /help — показать справку"
    )


@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Обработчик команды /help"""
    await message.reply_text(
        "📖 **Справка по боту**\n\n"
        "**Команды:**\n"
        "• /all или @all — упомянуть всех участников группы\n"
        "• /help — показать эту справку\n\n"
        "**Важно:**\n"
        "• Бот должен быть администратором группы\n"
        "• Бот получает список участников автоматически"
    )


async def tag_all_members(client: Client, message: Message):
    """Упоминание всех участников группы"""
    # Проверяем, что это группа
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply_text("⚠️ Эта команда работает только в группах!")
        return
    
    caller_id = message.from_user.id if message.from_user else None
    
    try:
        # Получаем список всех участников группы
        mentions = []
        async for member in client.get_chat_members(message.chat.id):
            user = member.user
            
            # Пропускаем ботов и того, кто вызвал команду
            if user.is_bot:
                continue
            if caller_id and user.id == caller_id:
                continue
            
            # Формируем упоминание
            if user.username:
                mentions.append(f"@{user.username}")
            else:
                name = user.first_name
                if user.last_name:
                    name += f" {user.last_name}"
                mentions.append(f"[{name}](tg://user?id={user.id})")
        
        if not mentions:
            await message.reply_text("🤷 Некого упоминать!")
            return
        
        # Разбиваем на части, если много участников
        chunk_size = 50
        for i in range(0, len(mentions), chunk_size):
            chunk = mentions[i:i + chunk_size]
            text = " ".join(chunk)
            await message.reply_text(text)
    
    except Exception as e:
        logger.error(f"Ошибка при получении участников: {e}")
        await message.reply_text(
            "❌ Не удалось получить список участников.\n"
            "Убедись, что бот — администратор группы."
        )


@app.on_message(filters.command("all") & filters.group)
async def all_command(client: Client, message: Message):
    """Обработчик команды /all"""
    await tag_all_members(client, message)


@app.on_message(filters.regex(r"@all|@все") & filters.group)
async def at_all(client: Client, message: Message):
    """Обработчик @all в сообщениях"""
    await tag_all_members(client, message)


if __name__ == "__main__":
    logger.info("🚀 Бот запускается...")
    app.run()
