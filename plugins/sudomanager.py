import os
from telethon import events

CONFIG = "container_data/config.env"

# ---------- ENV HELPERS ----------

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
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")

# ---------- USER ID RESOLVER ----------

async def extract_id(bot, event, text):
    # reply support
    if event.is_reply:
        reply = await event.get_reply_message()
        return reply.sender_id

    # numeric id
    try:
        return int(text)
    except:
        pass

    # username / link
    try:
        entity = await bot.get_entity(text)
        return entity.id
    except:
        return None

# ---------- LOAD SUDO ----------

def load_sudo():
    data = read_env()
    sudo = data.get("SUDO", "")
    return [int(x) for x in sudo.split() if x.isdigit()]

# ---------- REGISTER ----------

def register(bot):

    bot.sudo_users = load_sudo()

    # ===== GET SUDO =====
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

    # ===== ADD SUDO =====
    @bot.on(events.NewMessage(pattern=r"^/setsudo(?:\s+(.+))?$"))
    async def setsudo(event):
        if event.sender_id != bot.owner_id:
            return

        target = event.pattern_match.group(1) or ""
        user_id = await extract_id(bot, event, target)

        if not user_id:
            return await event.reply("Invalid user.")

        if user_id == bot.owner_id:
            return await event.reply("Owner cannot be sudo.")

        if user_id in bot.sudo_users:
            return await event.reply("Already a sudo user.")

        bot.sudo_users.append(user_id)

        data = read_env()
        data["SUDO"] = " ".join(map(str, bot.sudo_users))
        write_env(data)

        await event.reply(f"Added `{user_id}` to sudo.")

    # ===== REMOVE SUDO =====
    @bot.on(events.NewMessage(pattern=r"^/delsudo(?:\s+(.+))?$"))
    async def delsudo(event):
        if event.sender_id != bot.owner_id:
            return

        target = event.pattern_match.group(1) or ""
        user_id = await extract_id(bot, event, target)

        if not user_id:
            return await event.reply("Invalid user.")

        if user_id not in bot.sudo_users:
            return await event.reply("User is not sudo.")

        bot.sudo_users.remove(user_id)

        data = read_env()
        data["SUDO"] = " ".join(map(str, bot.sudo_users))
        write_env(data)

        await event.reply(f"Removed `{user_id}` from sudo.")
