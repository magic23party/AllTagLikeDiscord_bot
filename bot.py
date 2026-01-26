"""
Telegram бот для тега всех участников группы (Pyrogram версия)
Получает список участников напрямую через API — не нужен Group Privacy!

Команды:
  /all или @all - упомянуть всех участников группы
  /info - справка на русском и английском
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
        "🔹 /info — справка"
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


@app.on_message(filters.command("info"))
async def info_command(client: Client, message: Message):
    """Обработчик команды /info"""
    await message.reply_text(
        "🇷🇺 **РУССКИЙ**\n\n"
        "Этот бот позволяет упомянуть всех участников группы одной командой.\n\n"
        "**Как использовать:**\n"
        "1. Добавьте бота в группу\n"
        "2. Назначьте бота администратором\n"
        "3. Напишите /all или @all в любом сообщении\n\n"
        "**Команды:**\n"
        "• /all — упомянуть всех (в начале сообщения)\n"
        "• @all или @все — упомянуть всех (в любом месте)\n"
        "• /info — эта справка\n\n"
        "Бот не упоминает того, кто вызвал команду.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🇬🇧 **ENGLISH**\n\n"
        "This bot allows you to mention all group members with one command.\n\n"
        "**How to use:**\n"
        "1. Add the bot to your group\n"
        "2. Make the bot an administrator\n"
        "3. Type /all or @all in any message\n\n"
        "**Commands:**\n"
        "• /all — mention everyone (at the start of message)\n"
        "• @all — mention everyone (anywhere in message)\n"
        "• /info — this help\n\n"
        "The bot does not mention the person who called the command."
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
