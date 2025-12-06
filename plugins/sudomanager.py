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

def stringify(sudo_list):
    return " ".join(str(x) for x in sudo_list)

async def resolve_id(bot, value):
    try:
        if value.isdigit():
            return int(value)
        entity = await bot.get_entity(value)
        return entity.id
    except:
        return None

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/setsudo(?:\s+(.*))?$"))
    async def setsudo(event):
        uid = event.sender_id
        sudo = bot.sudo_users
        if uid != bot.owner_id and uid not in sudo:
            return await event.reply("❌ Permission denied.")

        target = event.pattern_match.group(1)
        if not target:
            return await event.reply("Usage: `/setsudo <id or @username>`")

        resolved = await resolve_id(bot, target.strip())
        if not resolved:
            return await event.reply("❌ Invalid ID or username.")

        if resolved == bot.owner_id:
            return await event.reply("❌ Owner cannot be added as sudo. Already owner.")

        if resolved in sudo:
            return await event.reply("⚠️ Already a sudo user.")

        sudo.append(resolved)
        data = load_env()
        data["SUDO"] = stringify(sudo)
        save_env(data)
        bot.sudo_users = sudo

        await event.reply(f"✅ Added **{resolved}** as sudo.")

    @bot.on(events.NewMessage(pattern=r"^/delsudo(?:\s+(.*))?$"))
    async def delsudo(event):
        uid = event.sender_id
        sudo = bot.sudo_users
        if uid != bot.owner_id and uid not in sudo:
            return await event.reply("❌ Permission denied.")

        target = event.pattern_match.group(1)
        if not target:
            return await event.reply("Usage: `/delsudo <id or @username>`")

        resolved = await resolve_id(bot, target.strip())
        if not resolved:
            return await event.reply("❌ Invalid ID or username.")

        if resolved not in sudo:
            return await event.reply("❌ Not in sudo list.")

        sudo.remove(resolved)
        data = load_env()
        data["SUDO"] = stringify(sudo)
        save_env(data)
        bot.sudo_users = sudo

        await event.reply(f"🗑 Removed **{resolved}** from sudo.")

    @bot.on(events.NewMessage(pattern=r"^/getsudo$"))
    async def getsudo(event):
        uid = event.sender_id
        sudo = bot.sudo_users
        if uid != bot.owner_id and uid not in sudo:
            return await event.reply("❌ Permission denied.")

        if not sudo:
            return await event.reply("No sudo users added.")

        text = "🛡 **SUDO USERS**\n\n"
        for i in sudo:
            try:
                u = await bot.get_entity(i)
                name = u.first_name or "N/A"
                text += f"• `{i}` — {name}\n"
            except:
                text += f"• `{i}` — Unknown\n"

        await event.reply(text)
