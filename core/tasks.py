import asyncio
import random
import time
from celery import shared_task
from .models import Photo
from .telegram import send_telegram_notification
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_photo(photo_id, file_name):
    time.sleep(20)  # имитируем обработку
    random_number = random.randint(1, 2000)

    try:
        photo = Photo.objects.get(id=photo_id)
        photo.random_number = random_number
        photo.save()
        logger.info(f"Processed photo {photo_id}: {random_number}")

        # Отправляем уведомление в Telegram, если это 20-й файл
        if Photo.objects.count() % 20 == 0:
            asyncio.run(send_telegram_notification(f"Обработано 20 файлов! Последний: {file_name}, число: {random_number}"))
    except Photo.DoesNotExist:
        logger.error(f"Photo {photo_id} not found")
    except Exception as e:
        logger.error(e)
