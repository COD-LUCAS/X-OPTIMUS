import os
from telethon import events

PLUGIN_LINKS_FILE = "container_data/plugin_links.txt"


def save_plugin_link(name: str, url: str):
    name = name.strip().upper()
    url = url.strip()
    if not name or not url:
        return

    os.makedirs(os.path.dirname(PLUGIN_LINKS_FILE), exist_ok=True)

    links = []
    if os.path.exists(PLUGIN_LINKS_FILE):
        with open(PLUGIN_LINKS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" ", 1)
                if len(parts) != 2:
                    continue
                cmd, link = parts
                if cmd.upper() != name:
                    links.append((cmd, link))

    links.append((name, url))

    with open(PLUGIN_LINKS_FILE, "w", encoding="utf-8") as f:
        for cmd, link in links:
            f.write(f"{cmd} {link}\n")


def get_plugin_links():
    if not os.path.exists(PLUGIN_LINKS_FILE):
        return []
    links = []
    with open(PLUGIN_LINKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) != 2:
                continue
            cmd, link = parts
            links.append((cmd, link))
    return links


def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/plugins$"))
    async def list_plugins(event):
        uid = event.sender_id

        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")

        links = get_plugin_links()

        if not links:
            return await event.reply(
                "⚠ No external plugins installed.\n\n"
                "Try to make plugins and install them using `/install <url>`"
            )

        text = "📦 **Installed external plugins:**\n\n"
        for name, url in links:
            text += f"• `{name}` → {url}\n"

        await event.reply(text, link_preview=False)
