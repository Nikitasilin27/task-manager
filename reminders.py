from telegram import Bot
from telegram.error import InvalidToken
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
import logging
from crud import get_tasks, get_active_users
import os
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# Получаем токен из переменной окружения
token = os.environ.get("7822793225:AAFug__PTGhCEmMkPBii0I75KbsNHBuGXd8")
if not token:
    logger.error("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
    raise ValueError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")

try:
    bot = Bot(token)
    logger.info("Telegram Bot успешно инициализирован")
except InvalidToken as e:
    logger.error(f"Недействительный токен Telegram: {e}")
    raise

async def get_telegram_users():
    try:
        updates = await bot.get_updates(offset=-1, timeout=10)
        return [update.message.chat.id for update in updates if update.message]
    except Exception as e:
        logger.error(f"Ошибка при получении пользователей из Telegram: {str(e)}")
        return []

async def check_reminders():
    logger.info("Проверка напоминаний...")
    async for db in get_db():
        try:
            db_users = await get_active_users(db)  # Пользователи с задачами
            tg_users = await get_telegram_users()  # Пользователи из Telegram
            users = list(set(db_users + tg_users))  # Уникальный список
            for user_id in users:
                tasks = await get_tasks(db, user_id)
                for task in tasks:
                    if task.reminder and task.deadline and not task.completed:
                        deadline = task.deadline.astimezone(timezone.utc)
                        now = datetime.now(timezone.utc)
                        if (deadline - now).total_seconds() <= 3600:
                            logger.info(f"Напоминание для задачи {task.title} (user_id={user_id})")
                            await bot.send_message(chat_id=user_id, text=f"Напоминание: {task.title} (дедлайн: {deadline})")
        except Exception as e:
            logger.error(f"Ошибка при проверке напоминаний: {str(e)}")
        finally:
            await db.close()

def start_scheduler():
    scheduler.add_job(check_reminders, 'interval', minutes=1)
    scheduler.start()
    logger.info("Планировщик напоминаний запущен")
