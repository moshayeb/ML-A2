import os
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = (os.getenv("ANTHROPIC_API_KEY") or "").strip()

with open("config.json", "r", encoding="utf-8") as f:
    settings = json.load(f)

if isinstance(settings.get("system_prompt"), list):
    settings["system_prompt"] = "\n".join(settings["system_prompt"])

AGENT_NAME = settings["agent_name"]
