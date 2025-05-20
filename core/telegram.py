import telegram

async def send_telegram_notification(message):
    bot = telegram.Bot(token='TELEGRAM_BOT_TOKEN')
    chat_id = 'CHAT_ID'
    await bot.send_message(chat_id=chat_id, text=message)