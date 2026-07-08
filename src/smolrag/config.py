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

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_THINKING = os.environ.get("DEEPSEEK_THINKING", "1").lower() in ("1", "true", "yes")
DEEPSEEK_REASONING_EFFORT = os.environ.get("DEEPSEEK_REASONING_EFFORT", "high")
