"""
Telegram бот для тега всех участников группы
Команды:
  /all или @all - упомянуть всех участников группы
  /help - показать справку
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Словарь для хранения участников групп {chat_id: {user_id: username}}
group_members: dict[int, dict[int, str]] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот для упоминания всех участников группы.\n\n"
        "📝 Добавь меня в группу и дай права администратора.\n\n"
        "🔹 Используй /all или напиши @all чтобы упомянуть всех.\n"
        "🔹 /help — показать справку"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📖 <b>Справка по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "• /all или @all — упомянуть всех участников группы\n"
        "• /help — показать эту справку\n\n"
        "<b>Важно:</b>\n"
        "• Бот должен быть администратором группы\n"
        "• Бот запоминает участников, которые пишут в чат\n"
        "• Чем больше сообщений в группе, тем больше участников бот знает",
        parse_mode=ParseMode.HTML
    )


async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отслеживание участников группы по их сообщениям"""
    if update.effective_chat.type in ['group', 'supergroup']:
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        if user and not user.is_bot:
            if chat_id not in group_members:
                group_members[chat_id] = {}
            
            # Сохраняем username или имя пользователя
            if user.username:
                group_members[chat_id][user.id] = f"@{user.username}"
            else:
                # Если нет username, используем имя с HTML-ссылкой
                name = user.first_name
                if user.last_name:
                    name += f" {user.last_name}"
                group_members[chat_id][user.id] = f'<a href="tg://user?id={user.id}">{name}</a>'


async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Упоминание всех участников группы"""
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("⚠️ Эта команда работает только в группах!")
        return
    
    chat_id = update.effective_chat.id
    caller_id = update.effective_user.id
    
    if chat_id not in group_members or len(group_members[chat_id]) == 0:
        await update.message.reply_text(
            "😕 Пока не знаю участников этой группы.\n"
            "Подожди, пока люди напишут хотя бы одно сообщение."
        )
        return
    
    # Собираем упоминания всех, кроме вызывающего и ботов
    mentions = []
    for user_id, mention in group_members[chat_id].items():
        if user_id != caller_id:
            mentions.append(mention)
    
    if not mentions:
        await update.message.reply_text("🤷 Некого упоминать — ты единственный известный участник!")
        return
    
    # Разбиваем на части, если слишком много участников (лимит Telegram ~4096 символов)
    chunk_size = 50
    for i in range(0, len(mentions), chunk_size):
        chunk = mentions[i:i + chunk_size]
        message = " ".join(chunk)
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)


async def handle_at_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка @all в сообщениях"""
    if update.message and update.message.text:
        text = update.message.text.lower()
        if '@all' in text or '@все' in text:
            await tag_all(update, context)


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка новых участников группы"""
    if update.effective_chat.type in ['group', 'supergroup']:
        chat_id = update.effective_chat.id
        
        if chat_id not in group_members:
            group_members[chat_id] = {}
        
        for member in update.message.new_chat_members:
            if not member.is_bot:
                if member.username:
                    group_members[chat_id][member.id] = f"@{member.username}"
                else:
                    name = member.first_name
                    if member.last_name:
                        name += f" {member.last_name}"
                    group_members[chat_id][member.id] = f'<a href="tg://user?id={member.id}">{name}</a>'


async def left_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаление вышедших участников"""
    if update.effective_chat.type in ['group', 'supergroup']:
        chat_id = update.effective_chat.id
        left_user = update.message.left_chat_member
        
        if chat_id in group_members and left_user.id in group_members[chat_id]:
            del group_members[chat_id][left_user.id]


def main() -> None:
    """Запуск бота"""
    # Получаем токен из переменной окружения
    token = os.environ.get("BOT_TOKEN")
    
    if not token:
        logger.error("❌ Не задана переменная окружения BOT_TOKEN!")
        logger.error("Установите токен: export BOT_TOKEN='ваш_токен'")
        return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("all", tag_all))
    
    # Обработка новых и ушедших участников
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member))
    
    # Отслеживание сообщений для записи участников и обработка @all
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_at_all))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_members))
    
    # Запускаем бота
    logger.info("🚀 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
