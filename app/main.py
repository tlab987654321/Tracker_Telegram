Version = "1_0"
import logging
import os
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
#from telegram_bot import start, amount, transaction_type, category, description, error, cancel, help_command, show_today, show_week, show_month, menu_callback
from telegram_bot import *
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Constants for conversation states (must match telegram_bot.py)
#START, AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(5)
START, AMOUNT, CATEGORY, DESCRIPTION = range(4)

# Main function to run the bot
def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Initialize the bot with the token from environment variable
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for user interaction
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('cancel', cancel)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
            #TYPE: [CallbackQueryHandler(transaction_type)], # Removed Type
            CATEGORY: [CallbackQueryHandler(category)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Add the conversation handler to the bot
    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^(start|today|week|month)$"))
    application.add_handler(CommandHandler("today", show_today))
    application.add_handler(CommandHandler("week", show_week))
    application.add_handler(CommandHandler("month", show_month))
    application.add_handler(CommandHandler("summary", show_summary))
    application.add_handler(CallbackQueryHandler(summary_callback, pattern='^summary_'))


    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()
