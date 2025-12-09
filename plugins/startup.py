async def on_startup(bot):
    try:
        text = (
            "🔥 **X-OPTIMUS BOT STARTED** 🔥\n\n"
            "✅ System Online\n"
            "⚙️ Modules Loaded\n"
            "🚀 Ready to Execute Commands"
        )
        await bot.send_message("me", text)
    except Exception as e:
        print(f"Startup message failed: {e}")
