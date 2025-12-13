async def on_startup(bot):
    try:
        await bot.send_message("me", "X-OPTIMUS BOT STARTED | Online")
    except Exception as e:
        print(f"Startup message failed: {e}")
