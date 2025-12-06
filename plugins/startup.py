async def on_startup(bot):
    try:
        text = "𝗫-𝗢𝗣𝗧𝗜𝗠𝗨𝗦 𝗕𝗢𝗧 𝗦𝗧𝗔𝗥𝗧𝗘𝗗"

        # Send to Saved Messages
        await bot.send_message("me", text)

        # Send to owner
        owner_id = getattr(bot, "owner_id", None)
        if owner_id:
            await bot.send_message(owner_id, text)

        # Send to all sudo members
        sudo_users = getattr(bot, "sudo_users", [])
        for uid in sudo_users:
            try:
                await bot.send_message(uid, text)
            except:
                pass

    except Exception as e:
        print(f"Startup message failed: {e}")
