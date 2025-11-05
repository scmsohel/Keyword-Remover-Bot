from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler
)
import json
import asyncio
import os
from fastapi import FastAPI, Request
import uvicorn
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Render Environment Variables থেকে data load
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render Environment Variable
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Render Environment Variable

# Validate environment variables
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable সেট করা হয়নি!")
if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL environment variable সেট করা হয়নি!")

ADMINS = [5993295933]  # bot owner
DATA_FILE = "keywords.json"
BAN_FILE = "ban.json"

# ================= FORCE JOIN CONFIG =================
CHANNEL_ID = "@nextgentech_bd"  # আপনার চ্যানেল
CHANNEL_LINK = "https://t.me/nextgentech_bd"

# ================= JSON INIT =================
try:
    with open(DATA_FILE) as f:
        data = json.load(f)
except:
    data = {}

if os.path.exists(BAN_FILE):
    try:
        with open(BAN_FILE) as f:
            banned_groups = json.load(f)
    except:
        banned_groups = []
else:
    banned_groups = []


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def save_ban():
    with open(BAN_FILE, "w") as f:
        json.dump(banned_groups, f)

# ================= FASTAPI APP =================
app = FastAPI(title="Telegram Keyword Bot", description="FastAPI + Webhook Bot")

# ================= TELEGRAM BOT SETUP =================
# Fixed application builder for python-telegram-bot v21.7
telegram_app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

# ================= FORCE JOIN HELPERS =================
async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """চেক করে ইউজার চ্যানেলের member কিনা"""
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False


def join_verify_keyboard():
    """জয়েন এবং ভেরিফাই এর কী-বোর্ড"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            '📢 আমাদের চ্যানেলে জয়েন করুন', url=CHANNEL_LINK)],
        [InlineKeyboardButton(
            '✅ ভেরিফাই করুন', callback_data='verify_membership')]
    ])

# ================= MODIFIED START COMMAND =================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্টার্ট কমান্ড with force join"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # শুধু প্রাইভেট চ্যাটে ফোর্স জয়েন চেক
    if update.effective_chat.type == "private":
        if not await is_member(user_id, context):
            welcome_text = f"""
👋 হ্যালো {user_name}!

🤖 Keyword Remover Bot এ আপনাকে স্বাগতম!

বটটি ব্যবহার করতে আপনাকে আমাদের চ্যানেলে জয়েন করতে হবে।

চ্যানেলে জয়েন করে "ভেরিফাই করুন" বাটনে ক্লিক করুন।
"""
            await update.message.reply_text(welcome_text, reply_markup=join_verify_keyboard())
            return

    # যদি ইতিমধ্যে মেম্বার হয় বা গ্রুপে থাকে
    welcome_text = f"""
👋 হ্যালো {user_name}!

🤖 Keyword Remover Bot এ আপনাকে স্বাগতম!

এই বটটি আপনার গ্রুপে স্বয়ংক্রিয়ভাবে স্প্যাম মেসেজ ডিলিট করে।
"""
    await update.message.reply_text(welcome_text)

# ================= VERIFY MEMBERSHIP CALLBACK =================
async def verify_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ভেরিফাই মেম্বারশিপ কলব্যাক"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_name = query.from_user.first_name

    if await is_member(user_id, context):
        await query.edit_message_text(
            f"✅ ধন্যবাদ {user_name}!\n\n"
            "আপনি সফলভাবে ভেরিফাই করেছেন।\n\n"
            "এখন আপনি বটের সকল কমান্ড ব্যবহার করতে পারবেন!\n\n"
            "Help দেখতে /help লিখুন।"
        )
    else:
        await query.edit_message_text(
            f"❌ {user_name}, আপনি এখনো আমাদের চ্যানেলে জয়েন করেননি।\n\n"
            "অনুগ্রহ করে প্রথমে চ্যানেলে জয়েন করে আবার ভেরিফাই বাটনে ক্লিক করুন:",
            reply_markup=join_verify_keyboard()
        )

# ================= FIXED ADMIN CHECK =================
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed admin check with error handling"""
    user_id = update.effective_user.id
    chat = update.effective_chat

    # Bot owner always admin
    if user_id in ADMINS:
        return True

    # Private chat - no admin check needed
    if chat.type == "private":
        return False

    # Group/supergroup - check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception as e:
        print(f"Admin check error: {e}")
        return False

# ================= FIXED COMMANDS WITH ERROR HANDLING =================
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed add command with error handling"""
    try:
        chat_id = str(update.effective_chat.id)
        if chat_id in banned_groups:
            return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য।")
        await update.message.reply_text("Send me the keyword you want to add:")
        return ADD_KEYWORD
    except Exception as e:
        print(f"Error in start_add: {e}")
        return ConversationHandler.END


async def start_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed remove command with error handling"""
    try:
        chat_id = str(update.effective_chat.id)
        if chat_id in banned_groups:
            return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য।")
        await update.message.reply_text("Send me the keyword you want to remove:")
        return REMOVE_KEYWORD
    except Exception as e:
        print(f"Error in start_remove: {e}")
        return ConversationHandler.END


async def start_set_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed set_delay command with error handling"""
    try:
        chat_id = str(update.effective_chat.id)
        if chat_id in banned_groups:
            return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য।")
        await update.message.reply_text("⏱ How many seconds should the bot delay be?")
        return SET_DELAY
    except Exception as e:
        print(f"Error in start_set_delay: {e}")
        return ConversationHandler.END


async def list_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed list command with error handling"""
    try:
        chat_id = str(update.effective_chat.id)
        if chat_id in banned_groups:
            return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য。")
        group = get_group(update.effective_chat.id)
        if group["keywords"]:
            await update.message.reply_text("Keywords:\n" + "\n".join(group["keywords"]))
        else:
            await update.message.reply_text("No keywords set.")
    except Exception as e:
        print(f"Error in list_keywords: {e}")


async def start_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed start_bot command with error handling"""
    try:
        chat_id = str(update.effective_chat.id)
        if chat_id in banned_groups:
            return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য。")
        group = get_group(update.effective_chat.id)
        group["bot_active"] = True
        save_data()
        await update.message.reply_text("🟢 Bot is now active!")
    except Exception as e:
        print(f"Error in start_bot_cmd: {e}")


async def stop_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed stop_bot command with error handling"""
    try:
        chat_id = str(update.effective_chat.id)
        if chat_id in banned_groups:
            return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য。")
        group = get_group(update.effective_chat.id)
        group["bot_active"] = False
        save_data()
        await update.message.reply_text("🔴 Bot is now stopped!")
    except Exception as e:
        print(f"Error in stop_bot_cmd: {e}")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fixed status command with error handling"""
    try:
        chat_id = str(update.effective_chat.id)
        if chat_id in banned_groups:
            return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
        if not await is_admin(update, context):
            return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য।")
        group = get_group(update.effective_chat.id)
        keywords_count = len(group.get("keywords", []))
        deleted_count = group.get("deleted_count", 0)  # ✅ এখানে counter নেওয়া হলো
        await update.message.reply_text(
            f"Bot: {'On' if group.get('bot_active', False) else 'Off'}\n"
            f"Delay sec: {group.get('bot_delay', 5)}\n"
            f"Keywords: {keywords_count}\n"
            f"Deleted messages: {deleted_count}"  # ✅ নতুন line
        )
    except Exception as e:
        print(f"Error in status_cmd: {e}")

# ================= STATES =================
ADD_KEYWORD, REMOVE_KEYWORD, SET_DELAY = range(3)

# ================= HELPERS =================
def get_group(chat_id):
    chat_id = str(chat_id)
    if chat_id not in data:
        data[chat_id] = {
            "keywords": [],
            "bot_active": False,
            "bot_delay": 5,
            "deleted_count": 0  # ✅ নতুন: এই গ্রুপে কত মেসেজ delete হয়েছে track করবে
        }
        save_data()
    group = data[chat_id]
    if "keywords" not in group:
        group["keywords"] = []
    if "bot_active" not in group:
        group["bot_active"] = False
    if "bot_delay" not in group:
        group["bot_delay"] = 5
    if "deleted_count" not in group:
        group["deleted_count"] = 0  # ✅ safeguard, কোনো আগের data missing হলে
    return group



# ================= ORIGINAL COMMANDS =================
async def add_keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.effective_chat.id)
    keyword = update.message.text.lower()
    if keyword not in group["keywords"]:
        group["keywords"].append(keyword)
        save_data()
        await update.message.reply_text(f"✅ Keyword added: {keyword}")
    else:
        await update.message.reply_text("⚠️ This keyword already exists!")
    return ConversationHandler.END


async def remove_keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.effective_chat.id)
    keyword = update.message.text.lower()
    if keyword in group["keywords"]:
        group["keywords"].remove(keyword)
        save_data()
        await update.message.reply_text(f"✅ Keyword removed: {keyword}")
    else:
        await update.message.reply_text("⚠️ This keyword does not exist!")
    return ConversationHandler.END


async def set_delay_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.effective_chat.id)
    try:
        delay = int(update.message.text)
        group["bot_delay"] = delay
        save_data()
        await update.message.reply_text(f"✅ Bot delay set to {delay} seconds")
    except:
        await update.message.reply_text("❌ Invalid number! Please send a valid number of seconds.")
    return ConversationHandler.END

# ================= BAN / UNBAN =================
async def ban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য。")
    if chat_id not in banned_groups:
        banned_groups.append(chat_id)
        save_ban()
    if chat_id in data:
        del data[chat_id]
        save_data()
    await update.message.reply_text("🚫 এই গ্রুপটি ban করা হলো。")


async def unban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য。")
    if chat_id in banned_groups:
        banned_groups.remove(chat_id)
        save_ban()
        get_group(chat_id)  # ensures defaults
        save_data()
        await update.message.reply_text("✅ এই গ্রুপটি unban করা হলো。")
    else:
        await update.message.reply_text("⚠️ এই গ্রুপ ban list এ নেই。")

# ================= MESSAGE CHECK =================
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return
    group = get_group(chat_id)
    if not group.get("bot_active", False):
        return
    msg_text = update.message.text.lower()
    for kw in group.get("keywords", []):
        if kw in msg_text:
            await asyncio.sleep(group.get("bot_delay", 5))
            try:
                await update.message.delete()
                group["deleted_count"] += 1  # ✅ delete হলে counter বাড়ানো
                save_data()  # ✅ পরিবর্তন save করা হচ্ছে
            except:
                pass  # Ignore delete errors
            break



# ================= LEAVE / START GROUP =================
async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    group = get_group(chat_id)
    group["bot_active"] = False
    save_data()
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status == "administrator":
            await update.message.reply_text("বট working বন্ধ হইছে। এডমিন আমাকে leave দেন。")
        else:
            if chat_id in data:
                del data[chat_id]
                save_data()
            await update.message.reply_text("👋 Bye! Leaving the group...")
            await context.bot.leave_chat(chat_id)
    except:
        # If bot is already kicked, just clean data
        if chat_id in data:
            del data[chat_id]
            save_data()


async def start_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, আপনি start করতে পারবেন না。")
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য。")
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status != "administrator":
            await update.message.reply_text("⚠️ আমি admin না হলে কাজ করতে পারব না। আমাকে admin করুন。")
            return
        get_group(chat_id)  # ensure defaults
        await update.message.reply_text("✅ এই গ্রুপের জন্য bot আবার active করা হলো。")
    except:
        await update.message.reply_text("❌ বটটি এই গ্রুপে নেই। প্রথমে বটকে গ্রুপে add করুন。")

# ================= BOT OWNER COMMANDS =================
async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ শুধুমাত্র bot owner দেখতে পারবেন。")
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /group_info <group_id>")
    gid = context.args[0]
    info_text = ""
    if gid in banned_groups:
        info_text += f"🚫 Group {gid} is BANNED\n"
        kb = [[InlineKeyboardButton("Unban Group", callback_data=f"unban_{gid}")]]
    else:
        info = get_group(gid)
        status = "On" if info.get("bot_active", False) else "Off"
        delay = info.get("bot_delay", 5)
        keywords = "\n".join(info.get("keywords", [])) if info.get("keywords") else "No keywords"
        info_text += f"Group ID: {gid}\nBot: {status}\nDelay: {delay}\nKeywords:\n{keywords}"
        kb = [
            [InlineKeyboardButton("Start Bot", callback_data=f"startdel_{gid}"),
             InlineKeyboardButton("Stop Bot", callback_data=f"stopdel_{gid}")],
            [InlineKeyboardButton("Ban Group", callback_data=f"ban_{gid}"),
             InlineKeyboardButton("Unban Group", callback_data=f"unban_{gid}")]
        ]
    reply_markup = InlineKeyboardMarkup(kb) if kb else None
    await update.message.reply_text(info_text, reply_markup=reply_markup)


async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ শুধুমাত্র bot owner দেখতে পারবেন。")
    if not data and not banned_groups:
        return await update.message.reply_text("কোনো গ্রুপ পাওয়া যায়নি。")
    text = "Groups:\n"
    for gid in data:
        info = get_group(gid)
        deleted_count = info.get("deleted_count", 0)  # ✅ Added deleted message count
        text += f"{gid} | Bot: {'On' if info.get('bot_active', False) else 'Off'} | Delay: {info.get('bot_delay', 5)}s | Keywords: {len(info.get('keywords', []))} | Deleted: {deleted_count}\n"
    for gid in banned_groups:
        text += f"{gid} | 🚫 BANNED\n"
    await update.message.reply_text(text)

# ================= HELP COMMAND =================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না。")

    commands_list = [
        "/add - Add a keyword",
        "/remove - Remove a keyword",
        "/set_delay - Set bot delay in seconds",
        "/list - List keywords",
        "/start_bot - Start the bot",
        "/stop_bot - Stop the bot",
        "/status - Check bot status",
        "/leave_group - Bot leave the group",
        "/start_group - Restart bot in the group"
    ]

    help_text = "✅ Available commands (excluding bot owner commands):\n\n" + "\n".join(commands_list)
    await update.message.reply_text(help_text)

# ================= HELP OWNER COMMAND =================
async def help_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ শুধুমাত্র bot owner এই কমান্ডটি ব্যবহার করতে পারবেন。")

    owner_commands = [
        "/ban - Ban the group",
        "/unban - Unban the group",
        "/group_info <group_id> - Show specific group info",
        "/groups - Show all groups",
    ]

    help_text = "👑 BOT OWNER COMMANDS 👑\n\n" + "\n".join(owner_commands)
    await update.message.reply_text(help_text)

# ================= CALLBACK =================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_split = query.data.split("_")
    action = data_split[0]
    gid = data_split[1]
    info = get_group(gid)

    if action == "startdel":
        info["bot_active"] = True
        save_data()
        await query.message.reply_text(f"🟢 Group {gid} bot now active!")
    elif action == "stopdel":
        info["bot_active"] = False
        save_data()
        await query.message.reply_text(f"🔴 Group {gid} bot now stopped!")
    elif action == "ban":
        if gid in data:
            banned_groups.append(gid)
            del data[gid]
            save_data()
            save_ban()
            await query.message.reply_text(f"🚫 Group {gid} banned!")
    elif action == "unban":
        if gid in banned_groups:
            banned_groups.remove(gid)
            save_ban()
            get_group(gid)
            save_data()
            await query.message.reply_text(f"✅ Group {gid} unbanned!")

# ================= GROUP INFO COMMAND =================
ASK_GROUP_ID = range(1)

async def group_info_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ শুধুমাত্র bot owner এই কমান্ডটি ব্যবহার করতে পারবেন。")
    await update.message.reply_text("📩 দয়া করে গ্রুপ ID পাঠান যেটার তথ্য দেখতে চান:")
    return ASK_GROUP_ID


async def group_info_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.message.text.strip()
    if not (gid.lstrip("-").isdigit()):
        await update.message.reply_text("⚠️ সঠিক গ্রুপ ID দিন (সংখ্যা হওয়া লাগবে)。")
        return ASK_GROUP_ID

    if gid in banned_groups:
        info_text = f"🚫 Group {gid} is BANNED"
        kb = [[InlineKeyboardButton("Unban Group", callback_data=f"unban_{gid}")]]
    else:
        info = get_group(gid)
        if not info:
            await update.message.reply_text("⚠️ এই Group ID ডাটাবেসে পাওয়া যায়নি。")
            return ConversationHandler.END

        status = "On" if info.get("bot_active", False) else "Off"
        delay = info.get("bot_delay", 5)
        keywords = info.get("keywords", [])
        keyword_count = len(keywords)
        keyword_text = f"{keyword_count} keyword{'s' if keyword_count != 1 else ''}"
        deleted_count = info.get("deleted_count", 0)  # ✅ ADD THIS LINE

        info_text = (
            f"📊 Group ID: {gid}\n"
            f"🤖 Bot: {status}\n"
            f"⏱ Delay: {delay} sec\n"
            f"📝 Keywords: {keyword_text}\n"        # ✅ Keywords info
            f"🗑 Deleted messages: {deleted_count}"  # ✅ Deleted messages info added here
        )

        kb = [
            [InlineKeyboardButton("Start Bot", callback_data=f"startdel_{gid}"),
             InlineKeyboardButton("Stop Bot", callback_data=f"stopdel_{gid}")],
            [InlineKeyboardButton("Ban Group", callback_data=f"ban_{gid}"),
             InlineKeyboardButton("Unban Group", callback_data=f"unban_{gid}")],
            [InlineKeyboardButton("📝 Show Keywords", callback_data=f"showkw_{gid}")]
        ]

    reply_markup = InlineKeyboardMarkup(kb)
    await update.message.reply_text(info_text, reply_markup=reply_markup)
    return ConversationHandler.END

# ================== NEW: Show Keywords Callback ==================
async def show_keywords_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gid = query.data.split("_")[1]
    info = get_group(gid)

    if not info:
        await query.edit_message_text("⚠️ Group not found in database.")
        return

    keywords = info.get("keywords", [])
    if not keywords:
        kw_text = "❌ No keywords found for this group."
    else:
        kw_text = "📝 Keywords for this group:\n\n" + "\n".join(f"• {kw}" for kw in keywords)

    await query.edit_message_text(kw_text)

# ================= WEBHOOK ENDPOINTS =================
@app.get("/")
async def root():
    return {
        "status": "✅ Bot is running!", 
        "message": "Telegram Keyword Bot with FastAPI + Webhook",
        "webhook_url": WEBHOOK_URL
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "bot": "running"}

@app.post("/webhook")
async def webhook(request: Request):
    """Telegram webhook endpoint"""
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def on_startup():
    """Bot startup - set webhook"""
    try:
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Set webhook
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")
        logger.info("🤖 Bot is now running on Render.com with FastAPI!")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    """Bot shutdown"""
    try:
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("🛑 Bot stopped successfully")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# ================= BOT HANDLERS SETUP =================
def setup_handlers():
    """Setup all bot handlers"""
    # Conversation handlers
    add_conv = ConversationHandler(
        entry_points=[CommandHandler('add', start_add)],
        states={ADD_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_keyword_reply)]},
        fallbacks=[]
    )
    remove_conv = ConversationHandler(
        entry_points=[CommandHandler('remove', start_remove)],
        states={REMOVE_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_keyword_reply)]},
        fallbacks=[]
    )
    delay_conv = ConversationHandler(
        entry_points=[CommandHandler('set_delay', start_set_delay)],
        states={SET_DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_delay_reply)]},
        fallbacks=[]
    )

    group_info_handler = ConversationHandler(
        entry_points=[CommandHandler("group_info", group_info_start)],
        states={ASK_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_info_reply)]},
        fallbacks=[],
    )

    # Add all handlers
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CallbackQueryHandler(verify_membership_callback, pattern="^verify_membership$"))
    telegram_app.add_handler(CallbackQueryHandler(show_keywords_callback, pattern=r"^showkw_"))
    telegram_app.add_handler(group_info_handler)
    telegram_app.add_handler(CommandHandler("help", help_cmd))
    telegram_app.add_handler(CommandHandler("help_owner", help_owner))
    telegram_app.add_handler(add_conv)
    telegram_app.add_handler(remove_conv)
    telegram_app.add_handler(delay_conv)
    telegram_app.add_handler(CommandHandler("list", list_keywords))
    telegram_app.add_handler(CommandHandler("start_bot", start_bot_cmd))
    telegram_app.add_handler(CommandHandler("stop_bot", stop_bot_cmd))
    telegram_app.add_handler(CommandHandler("status", status_cmd))
    telegram_app.add_handler(CommandHandler("leave_group", leave_group))
    telegram_app.add_handler(CommandHandler("start_group", start_group))
    telegram_app.add_handler(CommandHandler("ban", ban_group))
    telegram_app.add_handler(CommandHandler("unban", unban_group))
    telegram_app.add_handler(CommandHandler("group_info", group_info))
    telegram_app.add_handler(CommandHandler("groups", list_groups))
    telegram_app.add_handler(CallbackQueryHandler(button_callback, pattern="startdel_|stopdel_|ban_|unban_"))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

# Initialize handlers
setup_handlers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)



