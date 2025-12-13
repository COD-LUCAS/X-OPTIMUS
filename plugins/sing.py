import os
import asyncio
import subprocess
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

        query = event.pattern_match.group(1)
        if not query:
            return await event.reply(
                "🎙️ **Sing – Voice Song Player**\n\n"
                "Usage: `/sing <song name or YouTube link>`\n"
                "Example: `/sing malare premam`"
            )

        status = await event.reply("🎵 Searching your song…")

        base = os.path.join(TEMP_DIR, f"sing_{event.id}")
        audio_m4a = base + ".m4a"
        audio_ogg = base + ".ogg"

        try:
            ytdlp_cmd = [
                "yt-dlp",
                "-f", "bestaudio",
                "-o", audio_m4a,
                query
            ]

            proc = await asyncio.create_subprocess_exec(
                *ytdlp_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()

            if not os.path.exists(audio_m4a):
                await status.edit("❌ Sing: failed to download audio")
                await asyncio.sleep(2)
                await status.delete()
                return

            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", audio_m4a,
                "-c:a", "libopus",
                "-b:a", "96k",
                audio_ogg
            ]

            proc = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()

            if not os.path.exists(audio_ogg):
                await status.edit("❌ Sing: conversion failed")
                await asyncio.sleep(2)
                await status.delete()
                return

            await bot.send_file(
                event.chat_id,
                audio_ogg,
                voice_note=True
            )

            await asyncio.sleep(0.5)
            await status.delete()

        except Exception:
            try:
                await status.edit("❌ Sing: error processing song")
                await asyncio.sleep(2)
                await status.delete()
            except:
                pass

        finally:
            for f in (audio_m4a, audio_ogg):
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
