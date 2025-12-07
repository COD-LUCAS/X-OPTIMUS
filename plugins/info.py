import os
import json
from telethon import events

VERSION_PATHS = [
    "version.json",
    "./version.json",
    "container_data/version.json",
    "/home/container/version.json"
]

def get_bot_version():
    for p in VERSION_PATHS:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    return json.load(f).get("version", "0.0.0")
            except:
                return "0.0.0"
    return "0.0.0"

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/info$"))
    async def info(event):
        uid = event.sender_id
        mode = bot.mode.lower()

        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return

        me = await bot.get_me()
        version = get_bot_version()

        try:
            plugin_count = len(bot.list_event_handlers())
        except:
            plugin_count = "Unknown"

        text = (
            "✦ **X-OPTIMUS BOT INFORMATION** ✦\n"
            "──────────────────────────\n\n"
            f"🤖 **Bot ID:** `{me.id}`\n"
            f"👑 **Owner ID:** `{bot.owner_id}`\n"
            f"🔧 **Mode:** `{bot.mode.upper()}`\n"
            f"📦 **Plugins Loaded:** `{plugin_count}`\n"
            f"🧩 **Bot Version:** `{version}`\n"
            f"🐍 **Python:** `{os.sys.version.split()[0]}`\n\n"
            "📂 **GitHub Repo:**\n"
            "[CLICK HERE](https://github.com/COD-LUCAS/X-OPTIMUS.git)\n"
        )

        img = "assets/info.jpg"

        if os.path.exists(img):
            await bot.send_file(event.chat_id, img, caption=text)
        else:
            await event.reply(text)
