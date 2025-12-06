import os
from telethon import events

CONFIG = "container_data/config.env"


# -------------------------------------------------------
# ENV LOAD / SAVE
# -------------------------------------------------------
def load_env():
    data = {}
    if os.path.exists(CONFIG):
        for line in open(CONFIG, "r"):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                data[k] = v
    return data


def save_env(data):
    with open(CONFIG, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")


# -------------------------------------------------------
# GET SUDO LIST
# -------------------------------------------------------
def get_sudo_list():
    data = load_env()
    return data.get("SUDO", "").split()


# -------------------------------------------------------
# REGISTER COMMANDS
# -------------------------------------------------------
def register(bot):

    # ============== CHECKER FUNCTION ====================
    def allowed(uid):
        return uid == bot.owner_id or uid in bot.sudo_users

    # ============== ADD SUDO =============================
    @bot.on(events.NewMessage(pattern=r"^/setsudo\s+(\d+)$"))
    async def add_sudo(event):
        uid = event.sender_id
        if not allowed(uid):
            return await event.reply("❌ Permission denied.")

        new_id = event.pattern_match.group(1)

        sudos = get_sudo_list()
        if new_id in sudos:
            return await event.reply("⚠️ Already a sudo member.")

        sudos.append(new_id)
        data = load_env()
        data["SUDO"] = " ".join(sudos)
        save_env(data)

        await event.reply(f"✅ Added `{new_id}` to sudo members.\nUse `/getsudo` to view all.")

    # ============== DELETE SUDO ===========================
    @bot.on(events.NewMessage(pattern=r"^/delsudo\s+(\d+)$"))
    async def del_sudo(event):
        uid = event.sender_id
        if not allowed(uid):
            return await event.reply("❌ Permission denied.")

        rm_id = event.pattern_match.group(1)

        sudos = get_sudo_list()
        if rm_id not in sudos:
            return await event.reply("⚠️ That user is not a sudo member.")

        sudos.remove(rm_id)
        data = load_env()
        data["SUDO"] = " ".join(sudos)
        save_env(data)

        await event.reply(f"🗑️ Removed `{rm_id}` from sudo members.")

    # ============== SHOW SUDO LIST =========================
    @bot.on(events.NewMessage(pattern=r"^/getsudo$"))
    async def get_sudo(event):
        uid = event.sender_id
        if not allowed(uid):
            return await event.reply("❌ Permission denied.")

        sudos = get_sudo_list()
        if not sudos:
            return await event.reply("❌ No sudo members found.")

        text = "🛡 **SUDO MEMBERS**\n━━━━━━━━━━━━━━\n"

        for sid in sudos:
            try:
                user = await bot.get_entity(int(sid))
                name = user.first_name or "Unknown"
                uname = f"@{user.username}" if user.username else "No username"
                text += f"👤 **{name}**\n🔗 `{sid}`\n{uname}\n\n"
            except:
                text += f"👤 `{sid}` (User not found)\n\n"

        await event.reply(text)
