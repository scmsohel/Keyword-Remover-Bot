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

BOT_TOKEN = "8309261403:AAHHfLeAYdFLeYoNEL0mDmNyAUgW5b_S57w"
ADMINS = [5993295933]  # bot owner
DATA_FILE = "keywords.json"
BAN_FILE = "ban.json"

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


# ================= STATES =================
ADD_KEYWORD, REMOVE_KEYWORD, SET_DELAY = range(3)

# ================= HELPERS =================


def get_group(chat_id):
    chat_id = str(chat_id)
    if chat_id not in data:
        data[chat_id] = {"keywords": [], "bot_active": False, "bot_delay": 5}
        save_data()
    group = data[chat_id]
    # Ensure all keys exist
    if "keywords" not in group:
        group["keywords"] = []
    if "bot_active" not in group:
        group["bot_active"] = False
    if "bot_delay" not in group:
        group["bot_delay"] = 5
    return group


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    if user_id in ADMINS:
        return True
    if chat.type in ["group", "supergroup"]:
        member = await context.bot.get_chat_member(chat.id, user_id)
        return member.status in ["administrator", "creator"]
    return False


async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনদের জন্য।")

# ================= COMMANDS =================


async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    await update.message.reply_text("Send me the keyword you want to add:")
    return ADD_KEYWORD


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


async def start_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    await update.message.reply_text("Send me the keyword you want to remove:")
    return REMOVE_KEYWORD


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


async def start_set_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    await update.message.reply_text("⏱ How many seconds should the bot delay be?")
    return SET_DELAY


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


async def list_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    group = get_group(update.effective_chat.id)
    if group["keywords"]:
        await update.message.reply_text("Keywords:\n" + "\n".join(group["keywords"]))
    else:
        await update.message.reply_text("No keywords set.")


async def start_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    group = get_group(update.effective_chat.id)
    group["bot_active"] = True
    save_data()
    await update.message.reply_text("🟢 Bot is now active!")


async def stop_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    group = get_group(update.effective_chat.id)
    group["bot_active"] = False
    save_data()
    await update.message.reply_text("🔴 Bot is now stopped!")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    group = get_group(update.effective_chat.id)
    keywords_count = len(group.get("keywords", []))
    await update.message.reply_text(
        f"Bot: {'On' if group.get('bot_active', False) else 'Off'}\n"
        f"Delay sec: {group.get('bot_delay', 5)}\n"
        f"Keywords: {keywords_count}"
    )

# ================= BAN / UNBAN =================


async def ban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        return await admin_only(update, context)
    if chat_id not in banned_groups:
        banned_groups.append(chat_id)
        save_ban()
    if chat_id in data:
        del data[chat_id]
        save_data()
    await update.message.reply_text("🚫 এই গ্রুপটি ban করা হলো।")


async def unban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        return await admin_only(update, context)
    if chat_id in banned_groups:
        banned_groups.remove(chat_id)
        save_ban()
        get_group(chat_id)  # ensures defaults
        save_data()
        await update.message.reply_text("✅ এই গ্রুপটি unban করা হলো।")
    else:
        await update.message.reply_text("⚠️ এই গ্রুপ ban list এ নেই।")

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
            await update.message.delete()
            break

# ================= LEAVE / START GROUP =================


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    group = get_group(chat_id)
    group["bot_active"] = False
    save_data()
    bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
    if bot_member.status == "administrator":
        await update.message.reply_text("বট working বন্ধ হইছে। এডমিন আমাকে leave দেন।")
    else:
        if chat_id in data:
            del data[chat_id]
            save_data()
        await update.message.reply_text("👋 Bye! Leaving the group...")
        await context.bot.leave_chat(chat_id)


async def start_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, আপনি start করতে পারবেন না।")
    if not await is_admin(update, context):
        return await admin_only(update, context)
    bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
    if bot_member.status != "administrator":
        await update.message.reply_text("⚠️ আমি admin না হলে কাজ করতে পারব না। আমাকে admin করুন।")
        return
    get_group(chat_id)  # ensure defaults
    await update.message.reply_text("✅ এই গ্রুপের জন্য bot আবার active করা হলো।")

# ================= BOT OWNER COMMANDS =================


async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ শুধুমাত্র bot owner দেখতে পারবেন।")
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /group_info <group_id>")
    gid = context.args[0]
    info_text = ""
    if gid in banned_groups:
        info_text += f"🚫 Group {gid} is BANNED\n"
        kb = [[InlineKeyboardButton(
            "Unban Group", callback_data=f"unban_{gid}")]]
    else:
        info = get_group(gid)
        status = "On" if info.get("bot_active", False) else "Off"
        delay = info.get("bot_delay", 5)
        keywords = "\n".join(info.get("keywords", [])) if info.get(
            "keywords") else "No keywords"
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
        return await update.message.reply_text("❌ শুধুমাত্র bot owner দেখতে পারবেন।")
    if not data and not banned_groups:
        return await update.message.reply_text("কোনো গ্রুপ পাওয়া যায়নি।")
    text = "Groups:\n"
    for gid in data:
        info = get_group(gid)
        text += f"{gid} | Bot: {'On' if info.get('bot_active', False) else 'Off'} | Delay: {info.get('bot_delay', 5)}s | Keywords: {len(info.get('keywords', []))}\n"
    for gid in banned_groups:
        text += f"{gid} | 🚫 BANNED\n"
    await update.message.reply_text(text)

# ================= HELP COMMAND =================


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in banned_groups:
        return await update.message.reply_text("❌ এই গ্রুপটি banned, কোনো command চলবে না।")

    # সমস্ত কমান্ড লিস্ট, BOT OWNER COMMANDS বাদে
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

    help_text = "✅ Available commands (excluding bot owner commands):\n\n" + \
        "\n".join(commands_list)
    await update.message.reply_text(help_text)

# ================= HELP OWNER COMMAND =================


async def help_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # শুধুমাত্র Bot Owner দেখতে পারবে
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ শুধুমাত্র bot owner এই কমান্ডটি ব্যবহার করতে পারবেন।")

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
    """Bot owner er jonno group info command start"""
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("❌ শুধুমাত্র bot owner এই কমান্ডটি ব্যবহার করতে পারবেন।")

    await update.message.reply_text("📩 দয়া করে গ্রুপ ID পাঠান যেটার তথ্য দেখতে চান:")
    return ASK_GROUP_ID


async def group_info_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner ID পাঠালে সেই group info দেখাবে"""
    gid = update.message.text.strip()

    # ✅ accept both positive and negative numbers (-100...)
    if not (gid.lstrip("-").isdigit()):
        await update.message.reply_text("⚠️ সঠিক গ্রুপ ID দিন (সংখ্যা হওয়া লাগবে)।")
        return ASK_GROUP_ID

    if gid in banned_groups:
        info_text = f"🚫 Group {gid} is BANNED"
        kb = [[InlineKeyboardButton(
            "Unban Group", callback_data=f"unban_{gid}")]]
    else:
        info = get_group(gid)
        if not info:
            await update.message.reply_text("⚠️ এই Group ID ডাটাবেসে পাওয়া যায়নি।")
            return ConversationHandler.END

        status = "On" if info.get("bot_active", False) else "Off"
        delay = info.get("bot_delay", 5)

        # ✅ Keyword count
        keywords = info.get("keywords", [])
        keyword_count = len(keywords)
        keyword_text = f"{keyword_count} keyword{'s' if keyword_count != 1 else ''}"

        info_text = (
            f"📊 Group ID: {gid}\n"
            f"🤖 Bot: {status}\n"
            f"⏱ Delay: {delay} sec\n"
            f"📝 Keywords: {keyword_text}"
        )

        kb = [
            [
                InlineKeyboardButton(
                    "Start Bot", callback_data=f"startdel_{gid}"),
                InlineKeyboardButton(
                    "Stop Bot", callback_data=f"stopdel_{gid}")
            ],
            [
                InlineKeyboardButton("Ban Group", callback_data=f"ban_{gid}"),
                InlineKeyboardButton(
                    "Unban Group", callback_data=f"unban_{gid}")
            ],
            [
                InlineKeyboardButton(
                    "📝 Show Keywords", callback_data=f"showkw_{gid}")
            ]
        ]

    reply_markup = InlineKeyboardMarkup(kb)
    await update.message.reply_text(info_text, reply_markup=reply_markup)
    return ConversationHandler.END


# ================== NEW: Show Keywords Callback ==================

async def show_keywords_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show keyword list for a specific group"""
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
        kw_text = "📝 Keywords for this group:\n\n" + \
            "\n".join(f"• {kw}" for kw in keywords)

    await query.edit_message_text(kw_text)


# ================= BOT INIT =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Conversation handlers
add_conv = ConversationHandler(
    entry_points=[CommandHandler('add', start_add)],
    states={ADD_KEYWORD: [MessageHandler(
        filters.TEXT & ~filters.COMMAND, add_keyword_reply)]},
    fallbacks=[]
)
remove_conv = ConversationHandler(
    entry_points=[CommandHandler('remove', start_remove)],
    states={REMOVE_KEYWORD: [MessageHandler(
        filters.TEXT & ~filters.COMMAND, remove_keyword_reply)]},
    fallbacks=[]
)
delay_conv = ConversationHandler(
    entry_points=[CommandHandler('set_delay', start_set_delay)],
    states={SET_DELAY: [MessageHandler(
        filters.TEXT & ~filters.COMMAND, set_delay_reply)]},
    fallbacks=[]
)

group_info_handler = ConversationHandler(
    entry_points=[CommandHandler("group_info", group_info_start)],
    states={
        ASK_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_info_reply)],
    },
    fallbacks=[],
)


# Add handler
app.add_handler(CallbackQueryHandler(
    show_keywords_callback, pattern=r"^showkw_"))
app.add_handler(group_info_handler)
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("help_owner", help_owner))
app.add_handler(add_conv)
app.add_handler(remove_conv)
app.add_handler(delay_conv)
app.add_handler(CommandHandler("list", list_keywords))
app.add_handler(CommandHandler("start_bot", start_bot_cmd))
app.add_handler(CommandHandler("stop_bot", stop_bot_cmd))
app.add_handler(CommandHandler("status", status_cmd))
app.add_handler(CommandHandler("leave_group", leave_group))
app.add_handler(CommandHandler("start_group", start_group))
app.add_handler(CommandHandler("ban", ban_group))
app.add_handler(CommandHandler("unban", unban_group))
app.add_handler(CommandHandler("group_info", group_info))
app.add_handler(CommandHandler("groups", list_groups))
app.add_handler(CallbackQueryHandler(button_callback,
                pattern="startdel_|stopdel_|ban_|unban_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

print("✅ Bot is now running!")
app.run_polling()
