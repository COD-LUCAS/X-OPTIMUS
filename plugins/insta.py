import os
import asyncio
import aiohttp
import re
from telethon import events

TEMP_DIR = "container_data/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/insta(?:\s+(.*))?$"))
    async def insta_dl(event):

        mode = bot.mode.lower()
        uid = event.sender_id
        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return await event.reply("❌ Private mode: only owner or sudo can use this command.")

        link = event.pattern_match.group(1)
        if not link:
            return await event.reply(
                "📸 **Instagram Downloader**\n\n"
                "Usage: `/insta <reel / post / story link>`"
            )

        # validate link
        if "instagram.com" not in link:
            return await event.reply("❌ Invalid Instagram link.")

        msg = await event.reply("⏳ Fetching media from Instagram...")

        try:
            clean_url = link.split("?")[0]
            out_file = os.path.join(TEMP_DIR, f"insta_{event.id}.mp4")

            # run yt-dlp to extract and download
            cmd = [
                "yt-dlp",
                "-f", "best",
                "-o", out_file,
                clean_url
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()

            if not os.path.exists(out_file):
                await msg.edit("❌ Failed to fetch Instagram media,just send only link autoinsta is active.")
                await asyncio.sleep(2)
                await msg.delete()
                return

            await bot.send_file(event.chat_id, out_file, caption="📥 **Downloaded from Instagram**")
            await msg.delete()

        except Exception as e:
            try:
                await msg.edit(f"❌ Error:\n`{str(e)}`")
                await asyncio.sleep(2)
                await msg.delete()
            except:
                pass
        finally:
            if os.path.exists(out_file):
                os.remove(out_file)
