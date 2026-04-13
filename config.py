import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PREFIX = os.getenv("PREFIX", "y!")

EMBED_COLORS = {
    "success": 0xB2F2BB,  # mint
    "error": 0xFFADAD,  # rose
    "warning": 0xFFD6A5,  # orange
    "info": 0xA0C4FF,  # periwinkle
    "landmine": 0xE57373,  # red
    "fun": 0xBDB2FF,  # lavender
    "utility": 0x9BF6FF,  # teal
}

EMOJIS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "landmine": "💣",
    "boom": "💥",
    "shield": "🛡️",
    "loading": "🎌",
}
