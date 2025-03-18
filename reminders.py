from telegram import Bot
from telegram.error import InvalidToken, TelegramError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
import logging
from crud import get_tasks, get_active_users, update_task
import os
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# Получаем токен из переменной окружения
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
    raise ValueError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")

try:
    bot = Bot(token)
    logger.info("Telegram Bot успешно инициализирован")
except InvalidToken as e:
    logger.error(f"Недействительный токен Telegram: {e}")
    raise

async def check_reminders():
    logger.info("Проверка напоминаний...")
    
    async with await get_db() as db:
        try:
            # Получаем только активных пользователей из базы данных
            users = await get_active_users(db)
            
            for user_id in users:
                tasks = await get_tasks(db, user_id)
                for task in tasks:
                    # Если задача имеет включённое напоминание, задан дедлайн и не завершена
                    if task.reminder and task.deadline and not task.completed:
                        deadline = task.deadline.astimezone(timezone.utc)
                        now = datetime.now(timezone.utc)
                        time_diff = (deadline - now).total_seconds()
                        
                        # Если осталось меньше или равно 1 часу до дедлайна
                        if 0 < time_diff <= 3600:
                            logger.info(f"Отправка напоминания для задачи {task.title} (user_id={user_id})")
                            
                            try:
                                await bot.send_message(
                                    chat_id=user_id,
                                    text=f"Напоминание: {task.title} (дедлайн: {deadline.strftime('%Y-%m-%d %H:%M:%S UTC')})"
                                )
                                # Обновляем статус напоминания с помощью существующей функции update_task
                                await update_task(db, user_id, task.id, reminder=False)
                                logger.info(f"Напоминание для задачи {task.id} успешно отправлено")
                            except TelegramError as e:
                                logger.error(f"Ошибка при отправке напоминания пользователю {user_id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Ошибка при проверке напоминаний: {str(e)}")

def start_scheduler():
    scheduler.add_job(check_reminders, 'interval', minutes=1)
    scheduler.start()
    logger.info("Планировщик напоминаний запущен")
