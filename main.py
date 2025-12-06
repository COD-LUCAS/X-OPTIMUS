import os
import importlib
import platform
import time
import asyncio
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
import threading
import requests
from flask import Flask

START_TIME = time.time()

def run(cmd):
    try:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        pass

def install_ffmpeg():
    try:
        test = subprocess.run("ffmpeg -version", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if test.returncode == 0:
            return
        run("apt update -y")
        run("apt install ffmpeg -y")
    except:
        pass

def install_python_packages():
    try:
        import PIL
    except:
        run("pip install pillow --no-cache-dir")

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
        break

if not loaded:
    print("config.env not found")
    exit()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING = os.getenv("STRING_SESSION")
OWNER = os.getenv("OWNER", "")

if not API_ID or not API_HASH or not STRING:
    print("Missing API credentials")
    exit()

API_ID = int(API_ID)
bot = TelegramClient(StringSession(STRING), API_ID, API_HASH)
plugins = {}

def load_version():
    try:
        if os.path.exists("version.txt"):
            return open("version.txt").read().strip()
    except:
        pass
    return "v1.0.0"

async def check_session():
    try:
        me = await bot.get_me()
        return f"VALID ({me.first_name})"
    except:
        return "INVALID"

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
            except:
                pass
    return total

async def auto_join():
    try:
        await bot(JoinChannelRequest("xoptimusbothelp"))
    except:
        pass

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
        return
    while True:
        try:
            requests.get(url)
        except:
            pass
        time.sleep(120)

def start_uptime_pinger():
    threading.Thread(target=uptime_pinger, daemon=True).start()

def start_webserver():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "X-OPTIMUS ONLINE"

    port = int(os.getenv("PORT", 8080))
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port),
        daemon=True
    ).start()

async def show_banner(version, platform_type, plugin_count, session_status):
    os.system("clear || cls")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 X-OPTIMUS STARTING…")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("▶ SYSTEM INFO")
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Platform:", platform_type)
    print("Version:", version)
    print()
    print("▶ BOT DETAILS")
    print("API ID:", API_ID)
    print("Plugins Loaded:", plugin_count)
    print("Session:", session_status)
    print()
    print("🟢 BOT ONLINE")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

async def start():
    version = load_version()
    total = load_plugins()
    platform_type = detect_platform()

    start_webserver()

    await bot.start()

    me = await bot.get_me()
    global OWNER
    if not OWNER:
        OWNER = str(me.id)

    bot.owner_id = int(OWNER)

    sudo_str = os.getenv("SUDO", "")
    bot.sudo_users = [int(x) for x in sudo_str.split()] if sudo_str else []

    bot.mode = os.getenv("MODE", "public").lower()
    bot.MODE = bot.mode.upper()

    if platform_type != "PANEL":
        start_uptime_pinger()

    await auto_join()

    for p in plugins.values():
        if hasattr(p, "on_startup"):
            try:
                await p.on_startup(bot)
            except:
                pass

    session_status = await check_session()
    await show_banner(version, platform_type, total, session_status)

bot.loop.run_until_complete(start())
bot.run_until_disconnected()
