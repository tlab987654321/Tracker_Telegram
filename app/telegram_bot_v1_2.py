from db import get_transactions_by_period
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters, CallbackContext
)
from db import save_data_to_db
import re

# Define categories
INCOME_CATEGORIES = ['Salary', 'Investment', 'Bonus', 'Other']
EXPENSE_CATEGORIES = ['Food', 'Medical', 'Travel', 'Groceries', 'Entertainment', 'Bills', 'Other']

# Define stages
START, AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(5)

# /help command handler
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🤖 *Expense Tracker Bot Help*\n\n"
        "Here's how you can interact with this bot:\n"
        "• /start – Begin a new transaction\n"
        "• /today – Show Today's transaction\n"
        "• /week – Show This Week's transaction\n"
        "• /month – Show This Month's transaction\n"
        "• /cancel – Cancel the current transaction\n"
        "• /help – Show this help message\n\n"
        "You’ll be guided step-by-step to record either income or Expense.\n"
        "Just follow the prompts. ✅",
        parse_mode="Markdown"
    )


# /start handler
async def start(update: Update, context: CallbackContext) -> int:
    # Show help only if no session is in progress
    is_fresh_session = not context.user_data

    context.user_data.clear()  # Clear any stale data

    if is_fresh_session:
        await update.message.reply_text(
            "👋 *Welcome to Expense Tracker Bot!*\n\n"
            "You can use this bot to quickly record income and Expenses.\n\n"
            "Run /help to see help message\n\n"
            "➡️ *Let’s get started! Enter the amount:*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Welcome back! Let’s continue. Please enter the amount:\n"
            "Run /help to see help message\n\n",
            parse_mode="Markdown"
        )

    return AMOUNT

# Welcome note
async def welcome(update: Update, context: CallbackContext) -> int:
    if context.user_data:
        # Resuming existing conversation
        await update.message.reply_text("You're already in a session. Type /cancel to end it.")
        return ConversationHandler.END

    return await help_command(update, context)  # Show menu instead


# /cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "❌ The session has been canceled.\n"
        "👉 Select /start to add a new transaction.\n"
        "👉 Select /help for help menu.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# Amount handler with validation
async def amount(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip()

    # Validate decimal format (max two decimals)
    if not re.match(r'^\d+(\.\d{1,2})?$', user_input):
        await update.message.reply_text(
            "❌ Invalid amount format.\n"
            "Please enter a valid number (e.g., 100, 100.50, 0.99).\n"
            "👉 Type /cancel to stop.",
            parse_mode="Markdown"
        )
        return AMOUNT

    context.user_data['amount'] = user_input

    await update.message.reply_text(
        "Is this an *Income* or *Expense*?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Income", callback_data='Income')],
            [InlineKeyboardButton("Expense", callback_data='Expense')]
        ])
    )
    return TYPE

# Type handler
async def transaction_type(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    user_input = query.data.lower()

    if user_input not in ['income', 'expense']:
        await query.message.reply_text(
            "❗ Please select either *Income* or *Expense*.\n👉 Type /cancel to stop.",
            parse_mode="Markdown"
        )
        return TYPE

    context.user_data['type'] = user_input
    categories = INCOME_CATEGORIES if user_input == 'income' else EXPENSE_CATEGORIES
    buttons = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]

    await query.message.reply_text(
        "📂 Please select a category:\n👉 Type /cancel to stop.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATEGORY

# Category handler
async def category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['category'] = query.data

    await query.message.reply_text(
        "📝 Please provide a description for this transaction.\n👉 Type /cancel to stop.",
        parse_mode="Markdown"
    )
    return DESCRIPTION

# Description handler
async def description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    data = context.user_data

    username = update.message.from_user.username or update.message.from_user.full_name
    save_data_to_db(
        data['amount'], data['type'], data['category'], data['description'], username
    )

    await update.message.reply_text(
        f"✅ *Transaction Saved:*\n"
        f"Amount: {data['amount']}\n"
        f"Type: {data['type'].title()}\n"
        f"Category: {data['category']}\n"
        f"Description: {data['description']}\n"
        f"User: {username}",
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "👉 Select /start to add a new transaction.\n"
            "Run /help to see help message\n\n",
        parse_mode="Markdown"
    )

    return ConversationHandler.END

# Format Table for printing reports
def format_transactions_table(records):
    if not records:
        return "No transactions found."

    header = f"{'Report'} {'Amount':<8}| {'Type':<7}| {'Category':<8}| {'User':<10}| {'Date':<4}| {'Desc'}\n"
    lines = [header, "-" * 58]
    for r in records:
        amount, t_type, category, user, timestamp, desc = r
        lines.append(f"{amount:<8}| {t_type:<7}| {category:<8}| {user:<10}| {timestamp.strftime('%Y-%m-%d'):<8}| {desc}")

    return "\n".join(lines)

# Handler to show Todays Records
async def show_today(update: Update, context: CallbackContext):
    today = datetime.now().date()
    records = get_transactions_by_period(today, today)
    await update.message.reply_text(f"*Today's Transactions:*\n\n```{format_transactions_table(records)}```", parse_mode='Markdown')

# Handler to show this Week Records
async def show_week(update: Update, context: CallbackContext):
    today = datetime.now().date()
    start = today - timedelta(days=today.weekday())  # Monday
    end = today
    records = get_transactions_by_period(start, end)
    await update.message.reply_text(f"*This Week's Transactions:*\n\n```{format_transactions_table(records)}```", parse_mode='Markdown')

# Handler to show this Month Records
async def show_month(update: Update, context: CallbackContext):
    today = datetime.now().date()
    start = today.replace(day=1)
    end = today
    records = get_transactions_by_period(start, end)
    await update.message.reply_text(f"*This Month's Transactions:*\n\n```{format_transactions_table(records)}```", parse_mode='Markdown')

# Fallback for unexpected inputs
async def error(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "❗ I didn't understand that. Please follow the instructions or use /cancel."
    )

#Menu Call back for Reports
async def menu_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    command = query.data
    if command == 'start':
        return await start(update, context)
    elif command == 'today':
        return await show_today(update, context)
    elif command == 'week':
        return await show_week(update, context)
    elif command == 'month':
        return await show_month(update, context)


# Exported conversation handler
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
        TYPE: [CallbackQueryHandler(transaction_type)],
        CATEGORY: [CallbackQueryHandler(category)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('help', help_command)],
)
