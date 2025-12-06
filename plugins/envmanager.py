import os
from telethon import events

CONFIG = "container_data/config.env"

def load_env():
    data = {}
    if os.path.exists(CONFIG):
        with open(CONFIG, "r") as f:
            for i in f:
                if "=" in i:
                    k, v = i.strip().split("=", 1)
                    data[k] = v
    return data


def save_env(data):
    with open(CONFIG, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")


def register(bot):

    # SETVAR
    @bot.on(events.NewMessage(pattern=r"^/setvar\s*(.*)"))
    async def setvar(event):
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")

        args = event.pattern_match.group(1).strip()

        if not args or "=" not in args:
            return await event.reply(
                "**Usage:**\n"
                "`/setvar KEY=value`"
            )

        key, value = args.split("=", 1)
        data = load_env()
        data[key] = value
        save_env(data)

        await event.reply(f"✅ `{key}` updated successfully.")

    # DELVAR
    @bot.on(events.NewMessage(pattern=r"^/delvar\s*(.*)"))
    async def delvar(event):
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")

        key = event.pattern_match.group(1).strip()

        if not key:
            return await event.reply(
                "**Usage:**\n"
                "`/delvar KEY`"
            )

        data = load_env()

        if key in data:
            del data[key]
            save_env(data)
            return await event.reply(f"🗑️ `{key}` removed.")
        else:
            return await event.reply("❌ Variable not found.")

    # GETVAR
    @bot.on(events.NewMessage(pattern=r"^/getvar\s*(.*)"))
    async def getvar(event):
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")

        key = event.pattern_match.group(1).strip()

        if not key:
            return await event.reply(
                "**Usage:**\n"
                "`/getvar KEY`\n\n"
                "Example:\n"
                "`/getvar GEMINI_API_KEY`"
            )

        data = load_env()

        if key not in data:
            return await event.reply("❌ Variable not found.")

        value = data[key]

        await event.reply(f"🔍 **Value for `{key}`:**\n```\n{value}\n```")
