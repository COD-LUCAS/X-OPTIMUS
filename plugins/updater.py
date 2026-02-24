import os
import shutil
import zipfile
import requests
from telethon import events

ZIP_URL = "https://github.com/COD-LUCAS/X-OPTIMUS/archive/refs/heads/main.zip"
SAFE_DIRS = ["container_data"]

def is_safe(path):
    for s in SAFE_DIRS:
        if path == s or path.startswith(s + "/"):
            return True
    return False

def register(bot):

    @bot.on(events.NewMessage(pattern=r"^/update$"))
    async def update(event):

        uid = event.sender_id

        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")

        msg = await event.reply("⬇️ Downloading update...")

        try:
            if os.path.exists("update_temp"):
                shutil.rmtree("update_temp")
            os.makedirs("update_temp", exist_ok=True)

            data = requests.get(ZIP_URL, timeout=20, verify=False).content
            open("update.zip", "wb").write(data)

        except Exception as e:
            return await msg.edit(f"❌ Download failed:\n`{e}`")

        await msg.edit("📦 Extracting update...")

        try:
            with zipfile.ZipFile("update.zip") as z:
                z.extractall("update_temp")
        except Exception as e:
            return await msg.edit(f"❌ Extraction failed:\n`{e}`")
        finally:
            if os.path.exists("update.zip"):
                os.remove("update.zip")

        extracted_root = os.listdir("update_temp")[0]
        extracted = os.path.join("update_temp", extracted_root)

        if os.path.isdir(os.path.join(extracted, "X-OPTIMUS")):
            extracted = os.path.join(extracted, "X-OPTIMUS")

        await msg.edit("♻️ Updating files...")

        try:
            for item in os.listdir("."):
                if item == "update_temp":
                    continue
                if is_safe(item):
                    continue
                if item.startswith(".git"):
                    continue

                if os.path.isfile(item):
                    os.remove(item)
                else:
                    shutil.rmtree(item)

            for item in os.listdir(extracted):
                src = os.path.join(extracted, item)
                dst = item

                if is_safe(dst):
                    continue

                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

        except Exception as e:
            return await msg.edit(f"❌ Update failed:\n`{e}`")

        shutil.rmtree("update_temp", ignore_errors=True)
        await msg.edit("✅ Update successful! Use /reboot")

