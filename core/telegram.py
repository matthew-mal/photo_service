import telegram
import logging

logger = logging.getLogger(__name__)


async def send_telegram_notification(message):
    bot = telegram.Bot(token="TELEGRAM_BOT_TOKEN")
    chat_id = "CHAT_ID"
    try:
        logger.info(f"Sending telegram notification to {chat_id}")
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info("Notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
