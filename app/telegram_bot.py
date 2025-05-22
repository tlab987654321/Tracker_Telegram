import importlib
import os
from dotenv import load_dotenv

#Version = "1_0"
Version = os.getenv("BOT_VERSION", "1_0")

# Load environment variables from .env file
module = importlib.import_module(f"telegram_bot_v{Version}")

# Automatically expose all non-private attributes from the module
for attr in dir(module):
    if not attr.startswith("_"):  # Skip private/internal names
        globals()[attr] = getattr(module, attr)