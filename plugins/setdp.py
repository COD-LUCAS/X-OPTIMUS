from telethon import events
from telethon.tl.functions.photos import UploadProfilePhotoRequest

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/setdp$"))
    async def setdp(event):

        mode = bot.mode.lower()
        uid = event.sender_id

        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return

        reply = await event.get_reply_message()
        if not reply or not reply.photo:
            return await event.reply("Reply to an image")

        file = await reply.download_media()
        await bot(UploadProfilePhotoRequest(
            file=await bot.upload_file(file)
        ))

        await event.reply("✅ Profile picture updated")
