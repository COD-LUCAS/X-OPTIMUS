import os
import time
import psutil
import platform
from datetime import datetime
from telethon import events, Button

START_TIME = time.time()

def get_mode():
    """Auto-detect bot mode from environment variables"""
    if os.getenv("PUBLIC_MODE") in ["False", "0", "false"]:
        return "Private"
    if os.getenv("OWNER_ONLY") in ["True", "1", "true"]:
        return "Private"
    return "Public"

def get_uptime():
    """Calculate uptime in human-readable format"""
    uptime_seconds = int(time.time() - START_TIME)
    
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

def get_system_info():
    """Get system resource usage"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return cpu, ram, disk
    except:
        return None, None, None

def get_platform():
    """Detect hosting platform"""
    if os.getenv("RENDER"):
        return "Render"
    if os.getenv("KOYEB_APP_ID"):
        return "Koyeb"
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return "Railway"
    if os.getenv("HEROKU_APP_NAME"):
        return "Heroku"
    if "container" in os.getcwd().lower():
        return "Panel"
    return "VPS/Local"

def startup_text(include_stats=False):
    """Generate startup message"""
    mode = get_mode()
    platform_name = get_platform()
    
    text = (
        "╔═══════════════════════════════╗\n"
        "║   🚀 𝗫-𝗢𝗣𝗧𝗜𝗠𝗨𝗦 𝗨𝗦𝗘𝗥𝗕𝗢𝗧   ║\n"
        "╚═══════════════════════════════╝\n\n"
        "┌─ 𝗕𝗢𝗧 𝗜𝗡𝗙𝗢 ─────────────────────┐\n"
        f"│ 🔐 Mode      : {mode}\n"
        f"│ 🌐 Platform  : {platform_name}\n"
        f"│ ⚡ Handler   : /\n"
        f"│ 🟢 Status    : Online\n"
        "└───────────────────────────────┘\n"
    )
    
    if include_stats:
        uptime = get_uptime()
        cpu, ram, disk = get_system_info()
        
        text += (
            "\n┌─ 𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗧𝗔𝗧𝗦 ──────────────────┐\n"
            f"│ ⏰ Uptime    : {uptime}\n"
        )
        
        if cpu is not None:
            text += (
                f"│ 💻 CPU       : {cpu}%\n"
                f"│ 🧠 RAM       : {ram}%\n"
                f"│ 💾 Disk      : {disk}%\n"
            )
        
        text += (
            f"│ 🐍 Python    : {platform.python_version()}\n"
            "└───────────────────────────────┘\n"
        )
    
    text += (
        "\n📋 Type /help to see available commands"
    )
    
    return text

def detailed_info(bot):
    """Generate detailed system information"""
    uptime = get_uptime()
    cpu, ram, disk = get_system_info()
    platform_name = get_platform()
    mode = get_mode()
    
    # Count loaded plugins
    plugin_count = 0
    try:
        plugin_folder = "plugins"
        if os.path.isdir(plugin_folder):
            plugin_count = len([f for f in os.listdir(plugin_folder) 
                               if f.endswith('.py') and f != '__init__.py'])
    except:
        pass
    
    text = (
        "╔═══════════════════════════════════╗\n"
        "║   📊 𝗗𝗘𝗧𝗔𝗜𝗟𝗘𝗗 𝗦𝗬𝗦𝗧𝗘𝗠 𝗜𝗡𝗙𝗢   ║\n"
        "╚═══════════════════════════════════╝\n\n"
        "┌─ 𝗕𝗢𝗧 𝗖𝗢𝗡𝗙𝗜𝗚𝗨𝗥𝗔𝗧𝗜𝗢𝗡 ───────────────┐\n"
        f"│ Owner ID    : {getattr(bot, 'owner_id', 'N/A')}\n"
        f"│ Bot Mode    : {mode}\n"
        f"│ Handler     : /\n"
        f"│ Plugins     : {plugin_count} loaded\n"
    )
    
    sudo_users = getattr(bot, 'sudo_users', [])
    if sudo_users:
        text += f"│ Sudo Users  : {len(sudo_users)}\n"
    
    text += "└──────────────────────────────────┘\n\n"
    
    text += (
        "┌─ 𝗦𝗬𝗦𝗧𝗘𝗠 𝗥𝗘𝗦𝗢𝗨𝗥𝗖𝗘𝗦 ────────────────┐\n"
        f"│ Platform    : {platform_name}\n"
        f"│ Python      : {platform.python_version()}\n"
        f"│ Uptime      : {uptime}\n"
    )
    
    if cpu is not None:
        text += (
            f"│ CPU Usage   : {cpu}%\n"
            f"│ RAM Usage   : {ram}%\n"
            f"│ Disk Usage  : {disk}%\n"
        )
    
    text += (
        "└──────────────────────────────────┘\n\n"
        f"⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    return text

async def on_startup(bot):
    """Send startup message when bot starts"""
    try:
        message = startup_text(include_stats=False)
        message += "\n\n✅ Bot successfully deployed and ready!"
        
        # Send to saved messages
        await bot.send_message("me", message)
        
        # Optional: Send to owner if different from self
        owner_id = getattr(bot, 'owner_id', None)
        if owner_id:
            try:
                me = await bot.get_me()
                if owner_id != me.id:
                    await bot.send_message(owner_id, message)
            except:
                pass
    except Exception as e:
        print(f"Startup message failed: {e}")

def register(bot):
    """Register event handlers"""
    
    @bot.on(events.NewMessage(pattern=r"^/startup$"))
    async def startup_cmd(event):
        """Show startup message with basic info"""
        await event.reply(startup_text(include_stats=True))
    
    @bot.on(events.NewMessage(pattern=r"^/alive$"))
    async def alive_cmd(event):
        """Quick alive check"""
        uptime = get_uptime()
        mode = get_mode()
        
        text = (
            "✅ **X-OPTIMUS is Active!**\n\n"
            f"⏰ Uptime: `{uptime}`\n"
            f"🔐 Mode: `{mode}`\n"
            f"🌐 Platform: `{get_platform()}`\n"
            f"🐍 Python: `{platform.python_version()}`"
        )
        
        await event.reply(text)
    
    @bot.on(events.NewMessage(pattern=r"^/info$"))
    async def info_cmd(event):
        """Show detailed system information"""
        await event.reply(detailed_info(bot))
    
    @bot.on(events.NewMessage(pattern=r"^/ping$"))
    async def ping_cmd(event):
        """Check bot response time"""
        start = time.time()
        msg = await event.reply("🏓 Pinging...")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        await msg.edit(
            f"🏓 **Pong!**\n\n"
            f"⚡ Response Time: `{ping_time:.2f}ms`\n"
            f"⏰ Uptime: `{get_uptime()}`"
        )
    
    @bot.on(events.NewMessage(pattern=r"^/stats$"))
    async def stats_cmd(event):
        """Show resource statistics"""
        cpu, ram, disk = get_system_info()
        
        if cpu is None:
            await event.reply("❌ Unable to fetch system statistics")
            return
        
        # CPU emoji based on usage
        cpu_emoji = "🟢" if cpu < 50 else "🟡" if cpu < 80 else "🔴"
        ram_emoji = "🟢" if ram < 50 else "🟡" if ram < 80 else "🔴"
        disk_emoji = "🟢" if disk < 50 else "🟡" if disk < 80 else "🔴"
        
        text = (
            "📊 **System Resource Usage**\n\n"
            f"{cpu_emoji} CPU Usage: `{cpu}%`\n"
            f"{ram_emoji} RAM Usage: `{ram}%`\n"
            f"{disk_emoji} Disk Usage: `{disk}%`\n\n"
            f"⏰ Uptime: `{get_uptime()}`\n"
            f"🌐 Platform: `{get_platform()}`"
        )
        
        await event.reply(text)
    
    @bot.on(events.NewMessage(pattern=r"^/sysinfo$"))
    async def sysinfo_cmd(event):
        """Show detailed system info"""
        try:
            system_info = (
                "💻 **System Information**\n\n"
                f"**OS:** `{platform.system()} {platform.release()}`\n"
                f"**Architecture:** `{platform.machine()}`\n"
                f"**Processor:** `{platform.processor() or 'Unknown'}`\n"
                f"**Python:** `{platform.python_version()}`\n"
                f"**Platform:** `{get_platform()}`\n"
            )
            
            try:
                system_info += f"\n**Total RAM:** `{psutil.virtual_memory().total / (1024**3):.2f} GB`\n"
                system_info += f"**Total Disk:** `{psutil.disk_usage('/').total / (1024**3):.2f} GB`\n"
            except:
                pass
            
            await event.reply(system_info)
        except Exception as e:
            await event.reply(f"❌ Error fetching system info: {str(e)}")
