from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters, CallbackContext
)
from db import save_data_to_db

INCOME_CATEGORIES = ['Salary', 'Investment', 'Bonus', 'Other Income']
EXPENSE_CATEGORIES = ['Food', 'Travel', 'Entertainment', 'Bills', 'Other Expense']
BANK_ACCOUNT = ['Bank Account 1', 'Bank Account 2', 'Bank Account 3']

# Define stages of the conversation
START, AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(5)

# /start handler
async def start(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()  # Clear previous session
    await update.message.reply_text(
        "Welcome! Let's track your income and expenses. Please enter the amount:"
    )
    return AMOUNT

# /cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    await update.message.reply_text("The session has been canceled.")
    return ConversationHandler.END

# Amount input handler
async def amount(update: Update, context: CallbackContext) -> int:
    context.user_data['amount'] = update.message.text
    await update.message.reply_text(
        "Is this income or expense?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Income", callback_data='income')],
            [InlineKeyboardButton("Expense", callback_data='expense')],
        ])
    )
    return TYPE

# Type selection handler
async def transaction_type(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    user_input = query.data.lower()
    if user_input not in ['income', 'expense']:
        await query.message.reply_text("Please select 'Income' or 'Expense'.")
        return TYPE

    context.user_data['type'] = user_input

    # Select appropriate category list
    categories = INCOME_CATEGORIES if user_input == 'income' else EXPENSE_CATEGORIES

    # Generate inline keyboard buttons
    buttons = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]

    await query.message.reply_text(
        "Please select a category:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATEGORY

# Category selection handler
async def category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['category'] = query.data
    await query.message.reply_text("Please provide a description for the transaction.")
    return DESCRIPTION

# Description handler and save to DB
async def description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text

    amount = context.user_data['amount']
    transaction_type = context.user_data['type']
    category = context.user_data['category']
    description = context.user_data['description']
    username = update.message.from_user.username or update.message.from_user.full_name

    save_data_to_db(amount, transaction_type, category, description, username)

    await update.message.reply_text(
        f"✅ Transaction saved:\n"
        f"Amount: {amount}\nType: {transaction_type.title()}\n"
        f"Category: {category}\nDescription: {description}\nUser: {username}"
    )
    #return ConversationHandler.END

    # Send a second message with hyperlink to start again
    bot_username = context.bot.username  # Automatically gets bot's username
    start_link = f"https://t.me/{bot_username}?start=start"

    await update.message.reply_text(
        f"👉 Select [/start] to add a new transaction({start_link})",
        parse_mode="Markdown"
    )

    return ConversationHandler.END

# Optional: error handler
async def error(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("❗ Unexpected input. Please follow the steps.")

# Define the ConversationHandler to be imported in main.py
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start), CommandHandler('cancel', cancel)],
    states={
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
        TYPE: [CallbackQueryHandler(transaction_type)],
        CATEGORY: [CallbackQueryHandler(category)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
