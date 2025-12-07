import os
from telethon import events

CONFIG = "container_data/config.env"

def read_env():
    data = {}
    if os.path.exists(CONFIG):
        with open(CONFIG, "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k] = v
    return data

def write_env(data):
    with open(CONFIG, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/setvar\s+(.+)"))
    async def setvar(event):
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return

        arg = event.pattern_match.group(1)
        if "=" not in arg:
            return await event.reply("Format: `/setvar KEY=value`")

        key, value = arg.split("=", 1)

        platform = os.getenv("RENDER") or os.getenv("KOYEB_APP_ID")

        if platform:
            os.environ[key] = value
            return await event.reply(f"Updated `{key}` in Render/Koyeb environment.")

        data = read_env()
        data[key] = value
        write_env(data)
        await event.reply(f"Set `{key}` in config.env.")

    @bot.on(events.NewMessage(pattern=r"^/delvar\s+(.+)"))
    async def delvar(event):
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return

        key = event.pattern_match.group(1).strip()

        platform = os.getenv("RENDER") or os.getenv("KOYEB_APP_ID")

        if platform:
            if key in os.environ:
                del os.environ[key]
            return await event.reply(f"Deleted `{key}` from Render/Koyeb environment.")

        data = read_env()
        if key in data:
            del data[key]
            write_env(data)
            return await event.reply(f"Removed `{key}` from config.env.")
        else:
            return await event.reply("Variable not found.")

    @bot.on(events.NewMessage(pattern=r"^/getvar\s+(.+)"))
    async def getvar(event):
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return

        key = event.pattern_match.group(1).strip()

        platform = os.getenv("RENDER") or os.getenv("KOYEB_APP_ID")

        if platform:
            val = os.getenv(key)
            if val is None:
                return await event.reply("Not found.")
            return await event.reply(f"`{key}` = `{val}`")

        data = read_env()
        if key in data:
            return await event.reply(f"`{key}` = `{data[key]}`")
        else:
            return await event.reply("Not found.")
