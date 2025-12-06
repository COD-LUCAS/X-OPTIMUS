from telethon import events, Button
import time
import aiohttp
import base64
import json
import os
from pathlib import Path

start = time.time()

API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemma-3-12b-it",
]

# Storage
chatbot_enabled = {"dms": False, "groups": False}
chat_contexts = {}
model_states = {}
global_system_prompt = "You are a helpful AI assistant. Be concise, friendly, and informative."

# Config file path
CONFIG_PATH = "container_data/config.env"


def load_env_config():
    """Load configuration from config.env file"""
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def save_env_config(key, value):
    """Save or update a key in config.env file"""
    # Create directory if it doesn't exist
    Path(CONFIG_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing config
    lines = []
    key_exists = False
    
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#') and '=' in line:
                    existing_key = line.split('=', 1)[0].strip()
                    if existing_key == key:
                        lines.append(f'{key}="{value}"\n')
                        key_exists = True
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
    
    # Add new key if it doesn't exist
    if not key_exists:
        lines.append(f'{key}="{value}"\n')
    
    # Write back to file
    with open(CONFIG_PATH, 'w') as f:
        f.writelines(lines)


def get_gemini_api_key():
    """Get Gemini API key from config.env"""
    config = load_env_config()
    return config.get('GEMINI_API_KEY', '')

def register(bot):
    
    @bot.on(events.NewMessage(pattern=r"^/setvar(?:\s+(.*))?$"))
    async def setvar_command(event):
        """Set environment variables (Owner/Sudo only)"""
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")
        
        args = event.pattern_match.group(1)
        
        if not args or '=' not in args:
            return await event.reply(
                "**Usage:** `/setvar KEY=VALUE`\n\n"
                "**Example:**\n"
                "`/setvar GEMINI_API_KEY=your_api_key_here`\n\n"
                "**Available Keys:**\n"
                "• `GEMINI_API_KEY` - Gemini AI API key\n"
                "• `CHATBOT_SYSTEM_PROMPT` - Custom AI system prompt"
            )
        
        try:
            key, value = args.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            if not key or not value:
                return await event.reply("❌ Invalid format. Use: `/setvar KEY=VALUE`")
            
            # Save to config.env
            save_env_config(key, value)
            
            # Handle special cases
            if key == "CHATBOT_SYSTEM_PROMPT":
                global global_system_prompt
                global_system_prompt = value
                await event.reply(
                    f"✅ **System prompt updated!**\n\n"
                    f"New prompt: `{value[:100]}{'...' if len(value) > 100 else ''}`"
                )
            elif key == "GEMINI_API_KEY":
                await event.reply(
                    f"✅ **GEMINI_API_KEY saved successfully!**\n\n"
                    f"Key: `{value[:20]}...{value[-10:]}`\n\n"
                    f"Now you can use:\n"
                    f"`/chatbot on` - Enable chatbot\n"
                    f"`/ai your question` - Ask AI directly"
                )
            else:
                await event.reply(f"✅ **{key}** set to: `{value}`")
        
        except Exception as e:
            await event.reply(f"❌ Error saving config: {str(e)}")
    
    
    @bot.on(events.NewMessage(pattern=r"^/getvar(?:\s+(.*))?$"))
    async def getvar_command(event):
        """Get environment variable value (Owner/Sudo only)"""
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")
        
        args = event.pattern_match.group(1)
        
        if not args:
            # Show all vars
            config = load_env_config()
            if not config:
                return await event.reply("📝 No variables set in config.env")
            
            var_text = "**📝 Current Variables:**\n\n"
            for key, value in config.items():
                # Hide sensitive values
                if "KEY" in key or "TOKEN" in key or "SECRET" in key:
                    masked = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
                    var_text += f"• `{key}` = `{masked}`\n"
                else:
                    var_text += f"• `{key}` = `{value}`\n"
            
            await event.reply(var_text)
        else:
            key = args.strip()
            config = load_env_config()
            value = config.get(key)
            
            if value:
                # Mask sensitive values
                if "KEY" in key or "TOKEN" in key or "SECRET" in key:
                    masked = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
                    await event.reply(f"`{key}` = `{masked}`")
                else:
                    await event.reply(f"`{key}` = `{value}`")
            else:
                await event.reply(f"❌ Variable `{key}` not found")
    
    
    @bot.on(events.NewMessage(pattern=r"^/delvar(?:\s+(.*))?$"))
    async def delvar_command(event):
        """Delete environment variable (Owner/Sudo only)"""
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")
        
        args = event.pattern_match.group(1)
        
        if not args:
            return await event.reply("**Usage:** `/delvar KEY`\n\n**Example:** `/delvar GEMINI_API_KEY`")
        
        key = args.strip()
        
        try:
            config = load_env_config()
            if key not in config:
                return await event.reply(f"❌ Variable `{key}` not found")
            
            # Remove from config
            del config[key]
            
            # Rewrite file
            Path(CONFIG_PATH).parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                for k, v in config.items():
                    f.write(f'{k}="{v}"\n')
            
            await event.reply(f"✅ Variable `{key}` deleted successfully")
        
        except Exception as e:
            await event.reply(f"❌ Error deleting variable: {str(e)}")
    
    
    @bot.on(events.NewMessage(pattern=r"^/alive$"))
    async def alive(event):
        uptime = int(time.time() - start)
        await event.reply(f"Bot Alive! Uptime: {uptime}s")
    
    
    @bot.on(events.NewMessage(pattern=r"^/chatbot(?:\s+(.*))?$"))
    async def chatbot_control(event):
        """Control chatbot settings (Owner/Sudo only)"""
        uid = event.sender_id
        if uid != bot.owner_id and uid not in bot.sudo_users:
            return await event.reply("❌ Permission denied.")
        
        args = event.pattern_match.group(1)
        api_key = get_gemini_api_key()
        
        if not args:
            # Show status
            status_text = (
                "**🤖 Chatbot Status**\n\n"
                f"📱 DMs: `{'Enabled ✅' if chatbot_enabled['dms'] else 'Disabled ❌'}`\n"
                f"👥 Groups: `{'Enabled ✅' if chatbot_enabled['groups'] else 'Disabled ❌'}`\n"
                f"🔑 API Key: `{'Configured ✅' if api_key else 'Missing ❌'}`\n"
                f"💭 Active Contexts: `{len(chat_contexts)}`\n"
                f"🎯 System Prompt: `{global_system_prompt[:80]}...`\n\n"
                "**Commands:**\n"
                "`/chatbot on` - Enable for both DMs and groups\n"
                "`/chatbot off` - Disable for both\n"
                "`/chatbot on dm` - Enable only DMs\n"
                "`/chatbot on group` - Enable only groups\n"
                "`/chatbot off dm` - Disable only DMs\n"
                "`/chatbot off group` - Disable only groups\n"
                "`/chatbot clear` - Clear all contexts\n"
                "`/chatbot status` - Show this status"
            )
            return await event.reply(status_text)
        
        parts = args.strip().split()
        command = parts[0].lower()
        target = parts[1].lower() if len(parts) > 1 else "both"
        
        if command == "on":
            if not api_key:
                return await event.reply(
                    "❌ **GEMINI_API_KEY not configured!**\n\n"
                    "**How to get API key:**\n"
                    "1. Visit: https://aistudio.google.com/app/apikey\n"
                    "2. Sign in with Google account\n"
                    "3. Click 'Create API Key'\n"
                    "4. Copy the key\n\n"
                    "**Set it using:**\n"
                    "`/setvar GEMINI_API_KEY=your_api_key_here`"
                )
            
            if target in ["dm", "dms"]:
                chatbot_enabled["dms"] = True
                await event.reply("✅ Chatbot enabled for **DMs only**")
            elif target in ["group", "groups"]:
                chatbot_enabled["groups"] = True
                await event.reply("✅ Chatbot enabled for **Groups only**")
            else:
                chatbot_enabled["dms"] = True
                chatbot_enabled["groups"] = True
                await event.reply("✅ Chatbot enabled for **both DMs and Groups**")
        
        elif command == "off":
            if target in ["dm", "dms"]:
                chatbot_enabled["dms"] = False
                # Clear DM contexts
                for chat_id in list(chat_contexts.keys()):
                    if chat_id > 0:
                        del chat_contexts[chat_id]
                await event.reply("❌ Chatbot disabled for **DMs**")
            elif target in ["group", "groups"]:
                chatbot_enabled["groups"] = False
                # Clear group contexts
                for chat_id in list(chat_contexts.keys()):
                    if chat_id < 0:
                        del chat_contexts[chat_id]
                await event.reply("❌ Chatbot disabled for **Groups**")
            else:
                chatbot_enabled["dms"] = False
                chatbot_enabled["groups"] = False
                chat_contexts.clear()
                await event.reply("❌ Chatbot disabled for **both DMs and Groups**")
        
        elif command == "clear":
            chat_contexts.clear()
            model_states.clear()
            await event.reply("🗑️ All conversation contexts cleared!")
        
        elif command == "status":
            # Detailed status
            dm_chats = sum(1 for cid in chat_contexts if cid > 0)
            group_chats = sum(1 for cid in chat_contexts if cid < 0)
            
            status_text = (
                "**🤖 Detailed Chatbot Status**\n\n"
                f"📱 DMs: `{'Enabled ✅' if chatbot_enabled['dms'] else 'Disabled ❌'}`\n"
                f"👥 Groups: `{'Enabled ✅' if chatbot_enabled['groups'] else 'Disabled ❌'}`\n"
                f"🔑 API Key: `{'Configured ✅' if api_key else 'Missing ❌'}`\n\n"
                f"📊 **Statistics:**\n"
                f"💭 Active DM contexts: `{dm_chats}`\n"
                f"💬 Active Group contexts: `{group_chats}`\n"
                f"📈 Total contexts: `{len(chat_contexts)}`\n\n"
                f"🤖 **Current Models:**\n"
            )
            for i, model in enumerate(MODELS[:3]):
                status_text += f"{i+1}. `{model}`\n"
            
            status_text += f"\n🎯 **System Prompt:**\n`{global_system_prompt}`"
            
            await event.reply(status_text)
        
        else:
            await event.reply(
                f"❌ Unknown command: `{command}`\n\n"
                "Use `/chatbot` to see available commands."
            )
    
    
    @bot.on(events.NewMessage(incoming=True))
    async def auto_chatbot_handler(event):
        """Auto-respond to all messages when chatbot is enabled"""
        try:
            # Skip if message is from bot itself
            if event.out:
                return
            
            # Skip if it's a command
            if event.text and event.text.startswith('/'):
                return
            
            chat_id = event.chat_id
            is_dm = event.is_private
            is_group = event.is_group or event.is_channel
            
            # Check if chatbot is enabled for this type
            if is_dm and not chatbot_enabled["dms"]:
                return
            if is_group and not chatbot_enabled["groups"]:
                return
            
            # Check API key
            api_key = get_gemini_api_key()
            if not api_key:
                return
            
            # Get message text
            text = event.text or event.message.message or ""
            
            if len(text.strip()) < 2:
                return
            
            # Handle image if present
            image_bytes = None
            if event.photo:
                try:
                    image_bytes = await event.download_media(bytes)
                except Exception as e:
                    print(f"Error downloading image: {e}")
            
            # Get AI response
            response_text = text if text else "What do you see in this image?"
            ai_response = await get_ai_response(
                response_text, 
                chat_id, 
                api_key,
                image_bytes
            )
            
            if ai_response:
                await event.reply(ai_response)
        
        except Exception as e:
            print(f"Error in auto chatbot handler: {e}")
    
    
    @bot.on(events.NewMessage(pattern=r"^/ai(?:\s+(.*))?$"))
    async def ai_command(event):
        """Direct AI query command (available to all users)"""
        
        api_key = get_gemini_api_key()
        if not api_key:
            return await event.reply(
                "❌ AI feature not available. API key not configured.\n\n"
                "Ask admin to set it using:\n"
                "`/setvar GEMINI_API_KEY=your_key`"
            )
        
        prompt = event.pattern_match.group(1)
        image_bytes = None
        
        # Check for image in reply
        if event.reply_to_msg_id:
            replied = await event.get_reply_message()
            if replied.photo:
                try:
                    image_bytes = await replied.download_media(bytes)
                    if not prompt:
                        prompt = "What do you see in this image?"
                except Exception as e:
                    return await event.reply(f"❌ Failed to download image: {e}")
            elif replied.text and not prompt:
                prompt = replied.text
        
        if not prompt and not image_bytes:
            return await event.reply(
                "**Usage:**\n"
                "`/ai your question here`\n"
                "Or reply to an image with `/ai` or `/ai describe this`"
            )
        
        sent = await event.reply("🤔 Thinking...")
        
        try:
            ai_response = await get_ai_response(
                prompt,
                event.chat_id,
                api_key,
                image_bytes,
                use_context=False  # Don't save context for direct queries
            )
            
            await sent.edit(ai_response)
        
        except Exception as e:
            print(f"AI command error: {e}")
            await sent.edit("❌ An error occurred with the AI API.")


async def get_ai_response(message: str, chat_id: int, api_key: str, 
                         image_bytes: bytes = None, use_context: bool = True) -> str:
    """Get AI response from Gemini API"""
    
    if not api_key:
        return "❌ API key not configured"
    
    current_model_index = model_states.get(chat_id, 0)
    current_model = MODELS[current_model_index]
    
    try:
        api_url = f"{API_BASE_URL}{current_model}:generateContent?key={api_key}"
        
        # Build conversation context
        contents = [
            {
                "role": "user",
                "parts": [{"text": f"System: {global_system_prompt}"}]
            }
        ]
        
        # Add recent context if enabled
        if use_context and chat_id in chat_contexts:
            context = chat_contexts[chat_id]
            recent_context = context[-10:] if len(context) > 10 else context
            for msg in recent_context:
                contents.append({
                    "role": msg["role"],
                    "parts": [{"text": msg["text"]}]
                })
        
        # Build current message parts
        parts = [{"text": message}]
        if image_bytes:
            img_part = image_to_generative_part(image_bytes)
            if img_part:
                parts.append(img_part)
        
        contents.append({
            "role": "user",
            "parts": parts
        })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 1000,
                "temperature": 0.7
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 429:
                    # Rate limit - try next model
                    next_model_index = current_model_index + 1
                    if next_model_index < len(MODELS):
                        model_states[chat_id] = next_model_index
                        print(f"Rate limit hit, switching to: {MODELS[next_model_index]}")
                        return "⚠️ Rate limit reached. Switched to backup model. Please try again."
                    else:
                        return "❌ All models rate limited. Please try again later."
                
                data = await response.json()
                
                if (data and data.get("candidates") and 
                    len(data["candidates"]) > 0 and
                    data["candidates"][0].get("content") and
                    data["candidates"][0]["content"].get("parts")):
                    
                    ai_response = data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Update context if enabled
                    if use_context:
                        if chat_id not in chat_contexts:
                            chat_contexts[chat_id] = []
                        
                        context_msg = f"{message} [Image]" if image_bytes else message
                        chat_contexts[chat_id].append({"role": "user", "text": context_msg})
                        chat_contexts[chat_id].append({"role": "model", "text": ai_response})
                        
                        # Keep only last 20 messages
                        if len(chat_contexts[chat_id]) > 20:
                            chat_contexts[chat_id] = chat_contexts[chat_id][-20:]
                    
                    return ai_response
                else:
                    return "❌ Received unexpected response from AI."
    
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return f"❌ Error: {str(e)}"


def image_to_generative_part(image_bytes: bytes) -> dict:
    """Convert image bytes to Gemini API format"""
    try:
        data = base64.b64encode(image_bytes).decode('utf-8')
        return {
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": data
            }
        }
    except Exception as e:
        print(f"Error processing image: {e}")
        return None > 2
