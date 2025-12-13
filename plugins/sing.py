import os
import asyncio
from telethon import events

TEMP_DIR = "container_data/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/sing(?:\s+(.*))?$"))
    async def sing(event):

        mode = bot.mode.lower()
        uid = event.sender_id

        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return

        text = event.pattern_match.group(1)
        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text if reply else None

        if not text:
            return await event.reply(
                "🎙️ Sing – Voice Song Player\n\n"
                "Usage: `/sing <song name or YouTube link>`"
            )

        status = await event.reply("🎵 Searching your song...")

        base = os.path.join(TEMP_DIR, f"sing_{event.id}")
        m4a = base + ".m4a"
        ogg = base + ".ogg"

        try:
            target = text if text.startswith("http") else f"ytsearch1:{text}"

            await asyncio.create_subprocess_exec(
                "yt-dlp",
                "-f", "bestaudio",
                "--no-playlist",
                "-o", m4a,
                target,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            ).then(lambda p: p.wait())

            if not os.path.exists(m4a):
                raise Exception("download_failed")

            await asyncio.create_subprocess_exec(
                "ffmpeg", "-y",
                "-i", m4a,
                "-vn",
                "-c:a", "libopus",
                "-b:a", "96k",
                ogg,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            ).then(lambda p: p.wait())

            if not os.path.exists(ogg):
                raise Exception("convert_failed")

            await bot.send_file(event.chat_id, ogg, voice_note=True)

            await asyncio.sleep(0.3)
            await status.delete()

        except Exception:
            try:
                await status.edit("❌ Sing: Failed to process song")
                await asyncio.sleep(2)
                await status.delete()
            except:
                pass

        finally:
            for f in (m4a, ogg):
                if os.path.exists(f):
                    os.remove(f)
