async def on_startup(bot):
    try:
        text = (
            "🔥 **X-OPTIMUS BOT STARTED** 🔥\n\n"
            "✅ The system is now online.\n"
            "⚙️ All modules loaded successfully.\n"
            "🚀 Ready to execute commands!"
        )

        # Always send to saved messages (ME)
        await bot.send_message("me", text)

        sent_to = set()  # prevent duplicate sends

        owner_id = getattr(bot, "owner_id", None)
        if owner_id:
            await bot.send_message(owner_id, text)
            sent_to.add(owner_id)

        sudo_users = getattr(bot, "sudo_users", [])
        for uid in sudo_users:
            if uid not in sent_to:  # do NOT send again
                try:
                    await bot.send_message(uid, text)
                except:
                    pass

    except Exception as e:
        print(f"Startup message failed: {e}")
