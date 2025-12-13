import requests
from telethon import events

API = "https://api.sparky.biz.id/api/downloader/igdl?url="

def register(bot):

    @bot.on(events.NewMessage(pattern=r"https?://(www\.)?instagram\.com/[^\s]+"))
    async def insta(event):

        mode = bot.mode.lower()
        uid = event.sender_id

        # PRIVATE MODE → ONLY OWNER + SUDO CAN USE
        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return await event.reply("❌ Private mode: only owner or sudo can use Instagram download.")

        url = event.pattern_match.group(0)
        status = await event.reply("📥 Downloading from Instagram…")

        try:
            res = requests.get(API + url).json()

            if not res.get("status"):
                return await status.edit("❌ Failed to download. Invalid or unsupported link.")

            count = 0

            for item in res.get("data", []):
                media = item.get("url")
                if not media:
                    continue

                count += 1

                await bot.send_file(event.chat_id, media, reply_to=event.id)

            await status.delete()

            if count == 0:
                await event.reply("⚠ No downloadable media found.")
            else:
                await event.reply(f"✅ Sent {count} media file(s).")

        except Exception as e:
            await status.edit(f"⚠ Error: {e}")
