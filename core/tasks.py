import random
import time
from celery import shared_task
from .models import Photo
from .telegram import send_telegram_notification


@shared_task
def process_photo(photo_id, file_name):
    time.sleep(20)  # Имитация обработки
    random_number = random.randint(1, 1000)

    photo = Photo.objects.get(id=photo_id)
    photo.random_number = random_number
    photo.save()

    # Отправляем уведомление в Telegram, если это 20-й файл
    if Photo.objects.count() % 20 == 0:
        send_telegram_notification(f"Обработано 20 файлов! Последний: {file_name}, число: {random_number}")