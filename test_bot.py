from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update, context):
    await update.message.reply_text('سلام! ربات کار میکنه!')

def run_bot():
    application = ApplicationBuilder().token("5973522500:AAE4ztU9gCfa9P4xW9jjj9WSSSZUDAAjPfM").build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    run_bot()
