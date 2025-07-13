from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import pyktok as pyk
import os
import re

#init
load_dotenv()
api_key = os.getenv("telegram_token")
pyk.specify_browser('firefox')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm alive.")

async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    matches = re.findall(r"https?://vm\.tiktok\.com/\S+/?", text)
    if matches:
        for match in matches:
            pyk.save_tiktok(match)
        
        await update.message.reply_text(
            "Nice link!",
            reply_to_message_id=update.message.message_id
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(api_key).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_links))

    app.run_polling()
