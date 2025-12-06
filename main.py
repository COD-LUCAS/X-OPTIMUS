import os
import importlib
import platform
import time
import asyncio
import subprocess
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
import threading
import requests
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

START_TIME = time.time()

def run(cmd):
    try:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logger.error(f"Command failed: {cmd} - {e}")

def install_ffmpeg():
    try:
        test = subprocess.run("ffmpeg -version", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if test.returncode == 0:
            logger.info("FFmpeg already installed")
            return
        logger.info("Installing FFmpeg...")
        run("apt update -y")
        run("apt install ffmpeg -y")
        logger.info("FFmpeg installed successfully")
    except Exception as e:
        logger.error(f"FFmpeg installation failed: {e}")

def install_python_packages():
    try:
        import PIL
        logger.info("PIL already installed")
    except:
        logger.info("Installing Pillow...")
        run("pip install pillow --no-cache-dir")
        logger.info("Pillow installed successfully")

logger.info("=== X-OPTIMUS INITIALIZATION ===")
install_ffmpeg()
install_python_packages()

paths = [
    "container_data/config.env",
    "/home/container/container_data/config.env",
    "/home/container/config.env",
    "config.env"
]

loaded = False
for p in paths:
    if os.path.exists(p):
        load_dotenv(p)
        loaded = True
        logger.info(f"Config loaded from: {p}")
        break

if not loaded:
    logger.critical("config.env not found in any expected location")
    exit(1)

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING = os.getenv("STRING_SESSION")
OWNER = os.getenv("OWNER", "")

if not API_ID or not API_HASH or not STRING:
    logger.critical("Missing API credentials (API_ID, API_HASH, or STRING_SESSION)")
    exit(1)

API_ID = int(API_ID)
bot = TelegramClient(StringSession(STRING), API_ID, API_HASH)
plugins = {}

def load_version():
    try:
        if os.path.exists("version.txt"):
            version = open("version.txt").read().strip()
            logger.info(f"Version loaded: {version}")
            return version
    except Exception as e:
        logger.warning(f"Could not load version: {e}")
    return "v1.0.0"

async def check_session():
    try:
        me = await bot.get_me()
        return f"✓ VALID ({me.first_name})"
    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        return "✗ INVALID"

_original = bot.add_event_handler

def patched(handler, *a, **kw):
    async def wrap(event):
        uid = event.sender_id
        mode = getattr(bot, "mode", "public").lower()
        sudo = getattr(bot, "sudo_users", [])
        if mode == "private":
            if uid != bot.owner_id and uid not in sudo:
                return
        return await handler(event)
    return _original(wrap, *a, **kw)

bot.add_event_handler = patched

def load_plugins():
    total = 0
    folders = ["plugins", "container_data/user_plugins"]
    logger.info("Loading plugins...")
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if not f.endswith(".py") or f == "__init__.py":
                continue
            name = f[:-3]
            module_path = f"{folder.replace('/', '.')}.{name}"
            try:
                module = importlib.import_module(module_path)
                plugins[name] = module
                if hasattr(module, "register"):
                    module.register(bot)
                total += 1
                logger.info(f"  ✓ Loaded plugin: {name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to load {name}: {e}")
    logger.info(f"Total plugins loaded: {total}")
    return total

async def auto_join():
    try:
        await bot(JoinChannelRequest("xoptimusbothelp"))
        logger.info("Auto-joined support channel")
    except Exception as e:
        logger.warning(f"Could not auto-join channel: {e}")

def detect_platform():
    if os.getenv("RENDER"):
        return "RENDER"
    if os.getenv("KOYEB_APP_ID"):
        return "KOYEB"
    if "container" in os.getcwd().lower() or "ptero" in os.getcwd().lower():
        return "PANEL"
    return "LOCAL"

def get_auto_ping_url():
    if os.getenv("RENDER_EXTERNAL_URL"):
        return os.getenv("RENDER_EXTERNAL_URL")
    if os.getenv("KOYEB_URL"):
        return os.getenv("KOYEB_URL")
    return None

def uptime_pinger():
    url = get_auto_ping_url()
    if not url:
        logger.info("No auto-ping URL detected, uptime pinger disabled")
        return
    
    logger.info(f"Uptime pinger started for: {url}")
    consecutive_failures = 0
    
    while True:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                if consecutive_failures > 0:
                    logger.info("Uptime ping restored")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                logger.warning(f"Uptime ping returned {response.status_code}")
        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures == 1:
                logger.error(f"Uptime ping failed: {e}")
            elif consecutive_failures % 5 == 0:
                logger.error(f"Uptime ping still failing (attempt {consecutive_failures})")
        
        time.sleep(120)

def start_uptime_pinger():
    platform_type = detect_platform()
    if platform_type in ["RENDER", "KOYEB"]:
        logger.info("Starting uptime pinger thread...")
        threading.Thread(target=uptime_pinger, daemon=True).start()
    else:
        logger.info("Uptime pinger not needed for this platform")

def start_webserver():
    app = Flask(__name__)
    
    # Disable Flask's default logging for cleaner output
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    @app.route("/")
    def home():
        uptime = int(time.time() - START_TIME)
        return {
            "status": "online",
            "bot": "X-OPTIMUS",
            "uptime_seconds": uptime,
            "platform": detect_platform()
        }
    
    @app.route("/health")
    def health():
        return {"status": "healthy"}, 200

    # Smart port detection
    port = int(os.getenv("PORT", 8080))
    
    # Verify port is not already in use
    platform_type = detect_platform()
    if platform_type == "RENDER":
        # Render requires binding to 0.0.0.0 and the PORT env var
        port = int(os.getenv("PORT", 10000))
        logger.info(f"Render detected - using PORT={port}")
    
    logger.info(f"Starting web server on 0.0.0.0:{port}")
    
    def run_flask():
        try:
            app.run(host="0.0.0.0", port=port, threaded=True)
        except Exception as e:
            logger.error(f"Web server failed to start: {e}")
    
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Web server started successfully")

async def show_banner(version, platform_type, plugin_count, session_status):
    os.system("clear || cls")
    banner = f"""
╔══════════════════════════════════════════════════╗
║           🚀 X-OPTIMUS USERBOT 🚀               ║
╚══════════════════════════════════════════════════╝

┌─ SYSTEM INFORMATION ─────────────────────────────┐
│ Time     : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                  │
│ Platform : {platform_type:<38} │
│ Version  : {version:<38} │
│ Python   : {platform.python_version():<38} │
└──────────────────────────────────────────────────┘

┌─ BOT CONFIGURATION ──────────────────────────────┐
│ API ID   : {API_ID:<38} │
│ Plugins  : {plugin_count:<38} │
│ Session  : {session_status:<38} │
│ Mode     : {bot.MODE:<38} │
│ Owner    : {OWNER:<38} │
└──────────────────────────────────────────────────┘

┌─ STATUS ─────────────────────────────────────────┐
│ 🟢 BOT IS ONLINE AND READY                       │
└──────────────────────────────────────────────────┘
"""
    print(banner)
    logger.info("Bot startup complete - All systems operational")

async def start():
    logger.info("Starting bot initialization sequence...")
    
    version = load_version()
    platform_type = detect_platform()
    logger.info(f"Platform detected: {platform_type}")
    
    # Start web server first (important for Render)
    start_webserver()
    
    # Small delay to ensure webserver is up
    await asyncio.sleep(1)
    
    logger.info("Connecting to Telegram...")
    await bot.start()
    logger.info("Connected to Telegram successfully")

    me = await bot.get_me()
    global OWNER
    if not OWNER:
        OWNER = str(me.id)
        logger.info(f"Owner ID auto-detected: {OWNER}")

    bot.owner_id = int(OWNER)

    sudo_str = os.getenv("SUDO", "")
    bot.sudo_users = [int(x) for x in sudo_str.split()] if sudo_str else []
    if bot.sudo_users:
        logger.info(f"Sudo users: {bot.sudo_users}")

    bot.mode = os.getenv("MODE", "public").lower()
    bot.MODE = bot.mode.upper()
    logger.info(f"Bot mode: {bot.MODE}")

    # Start uptime pinger for Render/Koyeb
    start_uptime_pinger()

    await auto_join()

    total = load_plugins()

    # Call plugin startup hooks
    logger.info("Executing plugin startup hooks...")
    for p in plugins.values():
        if hasattr(p, "on_startup"):
            try:
                await p.on_startup(bot)
            except Exception as e:
                logger.error(f"Plugin startup hook failed: {e}")

    session_status = await check_session()
    await show_banner(version, platform_type, total, session_status)

try:
    bot.loop.run_until_complete(start())
    logger.info("Entering main event loop...")
    bot.run_until_disconnected()
except KeyboardInterrupt:
    logger.info("Bot stopped by user")
except Exception as e:
    logger.critical(f"Fatal error: {e}", exc_info=True)
finally:
    logger.info("Bot shutdown complete")
