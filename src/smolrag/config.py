import os
from pathlib import Path

from dotenv import load_dotenv


def _load_user_config() -> None:
    """
    Load environnement variables from ~/.config/smolrag/.env
    does not override previously defined env variables.
    """

    env_file = Path.home() / ".config" / "smolrag" / ".env"
    if env_file.exists():
        load_dotenv(env_file)


_load_user_config()

LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-v4-flash")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_THINKING = os.environ.get("LLM_THINKING", "1").lower() in ("1", "true", "yes")
LLM_REASONING_EFFORT = os.environ.get("LLM_REASONING_EFFORT", "high")
