import os
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_salon.settings')
django.setup()

from bot.telegram_bot import BeautySalonBot
from django.conf import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    bot = BeautySalonBot(settings.BOT_TOKEN)
    print("ربات در حال اجراست...")
    bot.application.run_polling()
