from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler, ContextTypes, CallbackQueryHandler, ApplicationBuilder
import json
import os
import asyncio

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render environment variable
ADMINS = [5993295933]
CHANNEL_ID = "@nextgentech_bd"
CHANNEL_LINK = "https://t.me/nextgentech_bd"

# ================= JSON FILES =================
DATA_FILE = "keywords.json"
BAN_FILE = "ban.json"

# Initialize JSON files
def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    if not os.path.exists(BAN_FILE):
        with open(BAN_FILE, "w") as f:
            json.dump([], f)

init_files()

# Load data
try:
    with open(DATA_FILE) as f:
        data = json.load(f)
except:
    data = {}

try:
    with open(BAN_FILE) as f:
        banned_groups = json.load(f)
except:
    banned_groups = []

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def save_ban():
    with open(BAN_FILE, "w") as f:
        json.dump(banned_groups, f)

# ================= FORCE JOIN SYSTEM =================
async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def join_verify_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📢 আমাদের চ্যানেলে জয়েন করুন', url=CHANNEL_LINK)],
        [InlineKeyboardButton('✅ ভেরিফাই করুন', callback_data='verify_membership')]
    ])

# ================= START COMMAND =================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if update.effective_chat.type == "private":
        if not await is_member(user_id, context):
            welcome_text = f"👋 হ্যালো {user_name}!\n\nবটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন।"
            await update.message.reply_text(welcome_text, reply_markup=join_verify_keyboard())
            return

    welcome_text = f"👋 হ্যালো {user_name}!\n\nKeyword Remover Bot এ আপনাকে স্বাগতম!"
    await update.message.reply_text(welcome_text)

# ================= VERIFY CALLBACK =================
async def verify_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if await is_member(user_id, context):
        await query.edit_message_text("✅ ধন্যবাদ! আপনি ভেরিফাই করেছেন।")
    else:
        await query.edit_message_text("❌ আপনি এখনো জয়েন করেননি।", reply_markup=join_verify_keyboard())

# ================= BOT SETUP =================
def main():
    # Check if BOT_TOKEN is set
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable is not set!")
        print("💡 Render.com এ Environment Variables এ BOT_TOKEN set করুন")
        return
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(verify_membership_callback, pattern="^verify_membership$"))
    
    print("✅ Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
