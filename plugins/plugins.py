import os
from telethon import events

PLUGIN_DIR = "container_data/user_plugins"

RAW_BASE = "https://gist.github.com/"  # Change if you want custom links


def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/plugins$"))
    async def list_plugins(event):

        uid = event.sender_id

        # Allowed only for OWNER + SUDO
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")

        if not os.path.exists(PLUGIN_DIR):
            return await event.reply("⚠ No plugin directory found.")

        files = [f for f in os.listdir(PLUGIN_DIR) if f.endswith(".py")]

        if not files:
            return await event.reply("⚠ No external plugins installed.")

        text = "📦 **Total external plugins:**\n\n"

        for f in files:
            name = f.replace(".py", "")
            url = f"{RAW_BASE}{name}"   # You can change URL format
            text += f"**{name}** : {url}\n\n"

        await event.reply(text, link_preview=False)
