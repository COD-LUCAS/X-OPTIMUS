import re
import asyncio
import aiohttp
from telethon import events

BING_URL = "https://www.bing.com/images/search"

def extract_images(html):
    return re.findall(r"murl&quot;:&quot;(https?://[^&]+)&quot;", html)

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/img(?:\s+(.*))?$"))
    async def img(event):

        mode = bot.mode.lower()
        uid = event.sender_id

        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return

        text = event.pattern_match.group(1)
        if not text:
            return await event.reply("Example: `/img cat 5`")

        parts = text.split()
        count = 5
        query = text

        if parts[-1].isdigit():
            count = int(parts[-1])
            query = " ".join(parts[:-1])

        if count < 1:
            count = 5
        if count > 8:
            count = 8

        await event.reply("🔍 Searching real photos only...")

        clean_query = (
            f"{query} "
            "-cartoon -anime -illustration -drawing -art -vector -clipart"
        )

        params = {
            "q": clean_query,
            "form": "HDRSC2",
            "first": "1",
            "qft": "+filterui:photo-photo"
        }

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(BING_URL, params=params, timeout=15) as r:
                    html = await r.text()

            images = extract_images(html)
            images = images[:count]

            if not images:
                return await event.reply("No real photos found.")

            for url in images:
                try:
                    await bot.send_file(
                        event.chat_id,
                        url,
                        reply_to=event.id
                    )
                    await asyncio.sleep(0.8)
                except:
                    pass

        except Exception as e:
            await event.reply(f"❌ Error while fetching images:\n`{e}`")
