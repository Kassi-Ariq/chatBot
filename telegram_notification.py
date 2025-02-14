import asyncio
from telegram import Bot

TOKEN = "7857863640:AAGPkT1OwJ4eKZ7oBytTW2N8gznK7AZEQwM"
CHAT_ID = "1359620075"
bot = Bot(token=TOKEN)


def telegramSendMessage(text):
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=text))