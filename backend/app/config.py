import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from backend/ regardless of CWD (uvicorn reload spawns subprocesses
# whose CWD may not match, so we resolve an absolute path here).
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"
if _ENV_FILE.exists():
    # Some hosts (e.g. the Claude Code harness) inject empty strings for well-known
    # secrets into subprocess environments. An empty env var masks the real .env
    # value under `override=False`, so clear empty entries before loading.
    for _k in ("ANTHROPIC_API_KEY", "FINNHUB_API_KEY", "NEWSAPI_API_KEY", "FRED_API_KEY"):
        if os.environ.get(_k, "__unset__") == "":
            os.environ.pop(_k, None)
    load_dotenv(_ENV_FILE, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    anthropic_api_key: str = ""
    claude_debate_model: str = "claude-opus-4-7"
    claude_parse_model: str = "claude-haiku-4-5-20251001"

    finnhub_api_key: str = ""
    newsapi_api_key: str = ""
    fred_api_key: str = ""

    database_url: str = "sqlite+aiosqlite:///./investment_agent.db"
    cache_dir: str = "./data_cache"
    knowledge_base_dir: str = "../knowledge_base"
    pine_script_dir: str = "../pine_scripts"

    daily_scan_cron: str = "30 8 * * MON-FRI"
    weekly_learning_cron: str = "0 18 * * SUN"
    monthly_skills_cron: str = "0 19 1 * *"

    debate_rounds: int = 2
    debate_allow_dissent: bool = True

    frontend_origin: str = "http://localhost:5173"

    @property
    def cache_path(self) -> Path:
        p = Path(self.cache_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def kb_path(self) -> Path:
        p = Path(self.knowledge_base_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def pine_path(self) -> Path:
        p = Path(self.pine_script_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
