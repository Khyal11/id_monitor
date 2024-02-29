import os
import asyncio
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
from added_users import load_added_users, save_added_users


# API_ID = int(os.environ.get("API_ID"))
# API_HASH = os.environ.get("API_HASH")
# BOT_TOKEN = os.environ.get("BOT_TOKEN")


Telegram = Client(
    "Telegram",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

added_users = load_added_users()
monitoring_active = False

async def send_notification(chat_id, message):
    try:
        await Telegram.send_message(int(chat_id), message)
    except Exception as e:
        print(f"Error sending notification: {str(e)}")

async def monitor_usernames():
    try:
        while monitoring_active:
            for username, user_info in added_users.copy().items():
                try:
                    user = await Telegram.get_users(username)
                    current_username = user.username if user.username else f"user_{user.id}"

                    if current_username and current_username != user_info["last_known_username"]:
                        print(
                            f'User {user.id} changed username from {user_info["last_known_username"]} to {current_username}.')

                        old_user_info = user_info.copy()

                        added_users[username]["last_known_username"] = current_username
                        added_users[username]["user_id"] = user.id

                        updated_current_username = added_users[username]["last_known_username"]

                        await send_notification("1716718736",
                                                f'User {user.id} changed username from {old_user_info["last_known_username"]} to @{updated_current_username}.')

                except Exception as user_error:
                    print(f"Error checking username for user {username}: {str(user_error)}")

            save_added_users(added_users)  # Save the data after the loop
            await asyncio.sleep(60)

    except Exception as e:
        await send_notification("1716718736", f"Error during monitoring: {str(e)}")
        save_added_users(added_users)
        await asyncio.sleep(10)

@Telegram.on_message(filters.private & filters.command(["start"]))
async def start_monitoring(_, update):
    global monitoring_active
    monitoring_active = True
    await update.reply_text("Monitoring started. I will notify you of any username changes.")
    await send_notification("1716718736", "Monitoring started.")
    asyncio.ensure_future(monitor_usernames())

@Telegram.on_message(filters.private & filters.command(["stop"]))
async def stop_monitoring(_, update):
    global monitoring_active
    monitoring_active = False
    await update.reply_text("Monitoring stopped.")
    await send_notification("1716718736", "Monitoring stopped.")

@Telegram.on_message(filters.private & filters.command(["adduser"]))
async def add_user(_, update):
    # Extract username from the command
    username = update.command[1].strip('@')

    try:
        # Use get_chat method to get information about the user by their username
        user = await Telegram.get_chat(username)
        user_id = user.id

        # Check if the user ID is already in the dictionary
        if any(user_id == info["user_id"] for info in added_users.values()):
            await update.reply_text(f"User with ID `{user_id}` already added.")
        else:
            # Add the user to the dictionary
            added_users[username] = {"user_id": user_id, "last_known_username": username}

            await update.reply_text(f"User @{username} added with ID: `{user_id}`")

    except Exception as e:
        await update.reply_text(f"Error: {e}")

@Telegram.on_message(filters.private & filters.command(["showlist"]))
async def show_user_list(_, update):
    if added_users:
        user_list_text = "\n".join(
            [f"@{added_users[username]['last_known_username']}: {added_users[username]['user_id']})"
             for username in added_users])
        await update.reply_text(f"List of added users:\n{user_list_text}")
    else:
        await update.reply_text("No users added. Use /adduser to add users.")

@Telegram.on_message(filters.private & filters.command(["getid"]))
async def get_user_id(_, update):
    username = update.command[1].strip('@')
    try:
        user_id = added_users.get(username, {}).get("user_id")
        if user_id:
            await update.reply_text(f"The user ID for {username} is: `{user_id}`")
        else:
            await update.reply_text(f"User {username} not found. Use /adduser to add them.")

    except Exception as e:
        await update.reply_text(f"Error: {e}")

@Telegram.on_message(filters.private & filters.command(["deleteuser"]))
async def delete_user(_, update):
    user_id_to_delete = int(update.command[1])
    for username, user_info in added_users.copy().items():
        if user_info["user_id"] == user_id_to_delete:
            del added_users[username]
    save_added_users(added_users)
    await update.reply_text(f"User with ID `{user_id_to_delete}` deleted successfully.")

asyncio.ensure_future(monitor_usernames())

if __name__ == "__main__":
    print("Bot is live.")
    Telegram.run()
