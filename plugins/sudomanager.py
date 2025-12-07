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

def extract_id(bot, text):
    try:
        return int(text)
    except:
        pass
    try:
        entity = bot.loop.run_until_complete(bot.get_entity(text))
        return entity.id
    except:
        return None

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/getsudo$"))
    async def getsudo(event):
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return
        
        if not bot.sudo_users:
            return await event.reply("No sudo users added.")

        msg = "**Sudo Users:**\n\n"
        for sid in bot.sudo_users:
            try:
                u = await bot.get_entity(sid)
                msg += f"- `{sid}` | {u.first_name}\n"
            except:
                msg += f"- `{sid}`\n"

        await event.reply(msg)

    @bot.on(events.NewMessage(pattern=r"^/setsudo\s+(.+)"))
    async def setsudo(event):
        uid = event.sender_id
        if uid != bot.owner_id:
            return

        target = event.pattern_match.group(1).strip()
        user_id = extract_id(bot, target)

        if not user_id:
            return await event.reply("Invalid user.")

        if user_id == bot.owner_id:
            return await event.reply("Owner cannot be added as sudo.")

        if user_id in bot.sudo_users:
            return await event.reply("Already a sudo user.")

        bot.sudo_users.append(user_id)

        platform = os.getenv("RENDER") or os.getenv("KOYEB_APP_ID")

        if platform:
            os.environ["SUDO"] = " ".join(str(x) for x in bot.sudo_users)
            return await event.reply(f"Added `{user_id}` to sudo (Render/Koyeb).")

        data = read_env()
        data["SUDO"] = " ".join(str(x) for x in bot.sudo_users)
        write_env(data)

        await event.reply(f"Added `{user_id}` to sudo.")

    @bot.on(events.NewMessage(pattern=r"^/delsudo\s+(.+)"))
    async def delsudo(event):
        uid = event.sender_id
        if uid != bot.owner_id:
            return

        target = event.pattern_match.group(1).strip()
        user_id = extract_id(bot, target)

        if not user_id:
            return await event.reply("Invalid user.")

        if user_id not in bot.sudo_users:
            return await event.reply("Not a sudo user.")

        bot.sudo_users = [x for x in bot.sudo_users if x != user_id]

        platform = os.getenv("RENDER") or os.getenv("KOYEB_APP_ID")

        if platform:
            os.environ["SUDO"] = " ".join(str(x) for x in bot.sudo_users)
            return await event.reply(f"Removed `{user_id}` from sudo (Render/Koyeb).")

        data = read_env()
        data["SUDO"] = " ".join(str(x) for x in bot.sudo_users)
        write_env(data)

        await event.reply(f"Removed `{user_id}` from sudo.")
