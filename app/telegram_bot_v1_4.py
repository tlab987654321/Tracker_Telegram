from db import get_transactions_by_period
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters, CallbackContext
)
from db import save_data_to_db
from collections import defaultdict
import re

# Define categories
INCOME_CATEGORIES = ['Salary', 'Investment', 'Bonus', 'Other']
EXPENSE_CATEGORIES = ['Food', 'Medical', 'Travel', 'Groceries', 'Entertainment', 'Bills', 'Other']

# Define stages
#START, AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(5)
START, AMOUNT, CATEGORY, DESCRIPTION = range(4) ## Removed TYPE

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
    context.user_data['type'] = 'expense'  # Force set type to expense

    # Show category options directly
    buttons = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in EXPENSE_CATEGORIES]

    await update.message.reply_text(
        "📂 Please select a category:\n👉 Type /cancel to stop.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATEGORY

# Removed Type handler as I'm using expenses only | Uncomment below for rollback
#############################################################################
# async def amount(update: Update, context: CallbackContext) -> int:
#     user_input = update.message.text.strip()

#     # Validate decimal format (max two decimals)
#     if not re.match(r'^\d+(\.\d{1,2})?$', user_input):
#         await update.message.reply_text(
#             "❌ Invalid amount format.\n"
#             "Please enter a valid number (e.g., 100, 100.50, 0.99).\n"
#             "👉 Type /cancel to stop.",
#             parse_mode="Markdown"
#         )
#         return AMOUNT

#     context.user_data['amount'] = user_input

#     await update.message.reply_text(
#         "Is this an *Income* or *Expense*?",
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup([
#             [InlineKeyboardButton("Income", callback_data='Income')],
#             [InlineKeyboardButton("Expense", callback_data='Expense')]
#         ])
#     )
#     return TYPE

# Type handler
# async def transaction_type(update: Update, context: CallbackContext) -> int:
#     query = update.callback_query
#     await query.answer()
#     user_input = query.data.lower()

#     if user_input not in ['income', 'expense']:
#         await query.message.reply_text(
#             "❗ Please select either *Income* or *Expense*.\n👉 Type /cancel to stop.",
#             parse_mode="Markdown"
#         )
#         return TYPE

#     context.user_data['type'] = user_input
#     categories = INCOME_CATEGORIES if user_input == 'income' else EXPENSE_CATEGORIES
#     buttons = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]

#     await query.message.reply_text(
#         "📂 Please select a category:\n👉 Type /cancel to stop.",
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup(buttons)
#     )
#     return CATEGORY
#############################################################################

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

# Show summary for Transactions

async def show_summary(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data='summary_today'),
            InlineKeyboardButton("📆 This Week", callback_data='summary_week'),
            InlineKeyboardButton("🗓️ This Month", callback_data='summary_month')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📊 Select a period to view your expense summary:",
        reply_markup=reply_markup
    )

async def summary_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    selection = query.data

    today = datetime.now().date()
    if selection == 'summary_today':
        start_date = end_date = today
        title = "📅 Today's Expenses"
    elif selection == 'summary_week':
        start_date = today - timedelta(days=today.weekday())  # Start of the week (Monday)
        end_date = today
        title = "📆 This Week's Expenses"
    elif selection == 'summary_month':
        start_date = today.replace(day=1)  # Start of the month
        end_date = today
        title = "🗓️ This Month's Expenses"
    else:
        await query.edit_message_text("❌ Invalid selection.")
        return

    # Retrieve transactions within the selected period
    records = get_transactions_by_period(start_date, end_date)

    if not records:
        await query.edit_message_text(f"{title}\n\nNo transactions found.")
        return

    # Aggregate expenses by category
    category_totals = defaultdict(float)
    total_expense = 0.0
    for record in records:
        amount, _, category, _, _, _ = record  # Adjust indices based on your record structure
        amount = float(amount)
        category_totals[category] += amount
        total_expense += amount

    # Format the summary message
    summary_lines = [f"{title}\n"]
    for category, amount in category_totals.items():
        summary_lines.append(f"• {category}: ₹{amount:.2f}")
    summary_lines.append(f"\n💰 Total: ₹{total_expense:.2f}")

    await query.edit_message_text("\n".join(summary_lines))





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
        #TYPE: [CallbackQueryHandler(transaction_type)], ## Removed Type
        CATEGORY: [CallbackQueryHandler(category)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('help', help_command)],
)
