import os
from telethon import events

def register(bot):

    @bot.on(events.NewMessage(pattern="^/list$"))
    async def list_commands(event):

        mode = bot.mode.lower()
        uid = event.sender_id

        # PRIVATE MODE → only owner & sudo allowed
        if mode == "private":
            if uid != bot.owner_id and uid not in bot.sudo_users:
                return  # silently block like other plugins

        # Reaction
        try:
            await event.react("📋")
        except:
            pass

        # Commands
        commands = {
            "**⚙️ BASIC COMMANDS**": {
                "/ping": "Check bot response speed",
                "/alive": "Check if bot is running",
                "/info": "Show bot information",
                "/id": "Get your user/chat ID",
                "/uptime": "Show bot uptime"
            },
            "**🔧 ADMIN COMMANDS**": {
                "/mode": "Switch public/private mode",
                "/setvar": "Set environment variable",
                "/delvar": "Delete environment variable",
                "/getvar": "show all variables",
                "/setsudo": "Add a sudo user",
                "/delsudo": "Remove a sudo user",
                "/getsudo": "show all sudo members",
                "/install <raw_url>": "Install a new plugin",
                "/remove <plugin>": "Remove installed plugin",
                "/plugins": "Show installed plugins",
                "/checkupdate": "Check for bot updates",
                "/update": "Update bot to latest version",
                "/reboot": "Restart the bot",
                "/setdp" : "change profile picture"
            },
            "**📥 DOWNLOADERS**": {
                "insta <url>": "Download Instagram media",
                "yt <url>": "Download YouTube video",
                "yta <url>": "Download YouTube audio",
                "img": "Image Downloader"
            },
            "**🎨 MEDIA TOOLS**": {
                "mp3": "Convert video to MP3 (reply to video)",
                "genimg <prompt>": "Generate AI image",
                "rbg": "Remove image background",
                "pdf": "Convert images to PDF",
                "url": "Upload media to Catbox",
                "sing": "sing the given song"
            },
            "**🤖 AI FEATURES**": {
                "chatbot": "Toggle auto AI replies"
            }
        }

        # Build Text
        txt = "**📋 ALL COMMANDS**\n\n"
        
        for category, cmds in commands.items():
            txt += f"{category}\n"
            for cmd, desc in cmds.items():
                txt += f"`{cmd}` - {desc}\n"
            txt += "\n"

        # Scan for user plugins
        plugin_dir = "container_data/user_plugins"
        if os.path.exists(plugin_dir):
            user_plugins = [
                f[:-3] for f in os.listdir(plugin_dir)
                if f.endswith(".py") and not f.startswith("_")
            ]

            if user_plugins:
                txt += f"**🔌 CUSTOM PLUGINS ({len(user_plugins)})**\n"
                for plugin in user_plugins:
                    txt += f"`{plugin}` - Installed plugin\n"
                txt += "\n"

        txt += "💡 Type `/menu` for quick view"

        await event.reply(txt, link_preview=False)
