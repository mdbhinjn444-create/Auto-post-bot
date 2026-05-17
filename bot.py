import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = [8508012498, 8225821294]
PASSWORD = "1910398591@#aA"

channels = []
members = set()
user_states = {}

sent_log = {}


def is_admin(user_id):
    return user_id in ADMIN_IDS


def is_member(user_id):
    return user_id in members


def has_access(user_id):
    return is_admin(user_id) or is_member(user_id)


def parse_selection(text, total):
    text = text.strip()
    if text.lower() == "all":
        return list(range(total))
    indices = []
    for part in text.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < total:
                indices.append(idx)
    return indices


def channel_list_text():
    if not channels:
        return None
    lines = []
    for i, ch in enumerate(channels, start=1):
        lines.append(f"{i}. {ch}")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "😎 Boss, write what you want to post within a minute on my order, "
        "and I will send your message to all groups/channels where I am admin 😻.\n\n"
        "If you do not know the bot's admin ID or password, "
        "you cannot get access. Contact admin ✆@A15287"
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_access(update.effective_user.id):
        await update.message.reply_text("You do not have access.")
        return
    text = channel_list_text()
    if not text:
        await update.message.reply_text("No groups/channels have been added yet.")
        return
    await update.message.reply_text("Added groups/channels:\n" + text)


async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not has_access(user_id):
        await update.message.reply_text("You do not have access.")
        return
    user_states[user_id] = {"state": "waiting_post"}
    await update.message.reply_text(
        "😻 Boss, share what you want to post and see what I do 😎"
    )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        user_states[user_id] = {"state": "waiting_target_id", "action": "add"}
        await update.message.reply_text("Boss, submit Telegram ID:")
    else:
        user_states[user_id] = {"state": "waiting_password_for_add"}
        await update.message.reply_text("😎 Boss, submit password ✅")


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not has_access(user_id):
        await update.message.reply_text("You do not have access.")
        return
    if is_admin(user_id):
        user_states[user_id] = {"state": "waiting_target_id", "action": "ban"}
        await update.message.reply_text("Submit Telegram ID to ban:")
    else:
        user_states[user_id] = {"state": "waiting_password_for_ban"}
        await update.message.reply_text("😎 Boss, submit password ✅")


async def addchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You do not have access.")
        return
    user_states[user_id] = {"state": "waiting_channel_id"}
    await update.message.reply_text(
        "Send the channel/group username or ID (e.g. @mychannel or -1001234567890 or https://t.me/+xxxx):"
    )


async def removepost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not has_access(user_id):
        await update.message.reply_text("You do not have access.")
        return
    if not channels:
        await update.message.reply_text("No channels/groups added yet.")
        return
    listing = channel_list_text()
    await update.message.reply_text(
        "From which channels/groups do you want to delete the post?\n"
        "Type the numbers (e.g. 1,2,3) or All:\n\n" + listing
    )
    user_states[user_id] = {"state": "waiting_channel_selection_remove"}


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state_info = user_states.get(user_id, {})
    state = state_info.get("state")
    text = update.message.text.strip()

    if state == "waiting_password_for_add":
        if text != PASSWORD:
            await update.message.reply_text("Password incorrect ❌")
            user_states.pop(user_id, None)
            return
        user_states[user_id] = {"state": "waiting_target_id", "action": "add"}
        await update.message.reply_text("Boss, submit Telegram ID:")
        return

    if state == "waiting_password_for_ban":
        if text != PASSWORD:
            await update.message.reply_text("Password incorrect ❌")
            user_states.pop(user_id, None)
            return
        user_states[user_id] = {"state": "waiting_target_id", "action": "ban"}
        await update.message.reply_text("Submit Telegram ID to ban:")
        return

    if state == "waiting_target_id":
        try:
            target_id = int(text)
        except ValueError:
            await update.message.reply_text("Please enter a valid numeric Telegram ID.")
            return
        action = state_info["action"]
        if action == "add":
            members.add(target_id)
            await update.message.reply_text(f"✅ {target_id} has been added as a member.")
        elif action == "ban":
            members.discard(target_id)
            await update.message.reply_text(f"❌ {target_id} has been removed from members.")
        user_states.pop(user_id, None)
        return

    if state == "waiting_channel_id":
        if text not in channels:
            channels.append(text)
            sent_log[channels.index(text)] = []
            await update.message.reply_text(f"✅ {text} has been added.")
        else:
            await update.message.reply_text(f"⚠️ {text} already exists.")
        user_states.pop(user_id, None)
        return

    if state == "waiting_post":
        if not channels:
            await update.message.reply_text(
                "No groups/channels added yet. Ask an admin to add channels first."
            )
            user_states.pop(user_id, None)
            return
        listing = channel_list_text()
        user_states[user_id] = {"state": "waiting_channel_selection_post", "post_content": text}
        await update.message.reply_text(
            "Which channels/groups do you want to post to?\n"
            "Type numbers (e.g. 1,2,3) or All:\n\n" + listing
        )
        return

    if state == "waiting_channel_selection_post":
        indices = parse_selection(text, len(channels))
        if not indices:
            await update.message.reply_text(
                "Invalid selection. Type numbers like 1,2,3 or All."
            )
            return
        post_content = state_info["post_content"]
        success = 0
        fail = 0
        for idx in indices:
            chat_id = channels[idx]
            try:
                sent_msg = await context.bot.send_message(chat_id=chat_id, text=post_content)
                if idx not in sent_log:
                    sent_log[idx] = []
                sent_log[idx].append((sent_msg.message_id, post_content))
                success += 1
            except Exception as e:
                print(f"Failed to send to {chat_id}: {e}")
                fail += 1
        await update.message.reply_text(
            f"Post complete!\nTotal selected: {len(indices)}\nSuccess: {success}\nFailed: {fail}"
        )
        user_states.pop(user_id, None)
        return

    if state == "waiting_channel_selection_remove":
        indices = parse_selection(text, len(channels))
        if not indices:
            await update.message.reply_text(
                "Invalid selection. Type numbers like 1,2,3 or All."
            )
            return
        user_states[user_id] = {
            "state": "waiting_delete_text",
            "del_indices": indices
        }
        await update.message.reply_text(
            "Type the exact post text you want to delete 😶"
        )
        return

    if state == "waiting_delete_text":
        target_text = text
        del_indices = state_info["del_indices"]
        total = len(del_indices)
        deleted = 0
        failed = 0
        for idx in del_indices:
            chat_id = channels[idx]
            messages = sent_log.get(idx, [])
            found = False
            for msg_id, msg_text in messages:
                if msg_text == target_text:
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                        sent_log[idx] = [
                            (mid, mt) for mid, mt in sent_log[idx]
                            if not (mid == msg_id and mt == target_text)
                        ]
                        deleted += 1
                        found = True
                        break
                    except Exception as e:
                        print(f"Failed to delete from {chat_id}: {e}")
                        failed += 1
                        found = True
                        break
            if not found:
                failed += 1
        await update.message.reply_text(
            f"TOTAL : {total}\nDeleted : {deleted}\nDeleted Fail : {failed}"
        )
        user_states.pop(user_id, None)
        return

    if not has_access(user_id):
        await update.message.reply_text(
            "You do not have access. You can only use /start and /add."
        )


async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("addchannel", addchannel_command))
    app.add_handler(CommandHandler("removepost", removepost_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is starting...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await app.updater.idle()
    await app.stop()
    await app.shutdown()


if __name__ == "__main__":
    asyncio.run(run_bot())
