import time
from telethon import events

def format_uptime(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return f"{d}d {h}h {m}m {s}s"

def register(bot):

    if not hasattr(bot, "START_TIME"):
        bot.START_TIME = time.time()

    @bot.on(events.NewMessage(pattern=r"^/uptime$"))
    async def uptime(event):
        uid = event.sender_id
        mode = bot.mode.lower()

        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return

        sec = int(time.time() - bot.START_TIME)
        uptime_text = format_uptime(sec)

        text = (
            "🔥 **X-OPTIMUS BOT UPTIME** 🔥\n\n"
            f"⏱ **Running Since:** `{uptime_text}`\n"
            "⚡ **Status:** Stable\n"
        )

        await event.reply(text)
