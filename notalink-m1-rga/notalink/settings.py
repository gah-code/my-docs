from __future__ import annotations
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    APP_NAME: str = "NotaLink"
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1])
    VAR_DIR: Path = Field(default_factory=lambda: Path("var"))
    DATA_DIR: Path = Field(default_factory=lambda: Path("var/data"))
    TRACES_DIR: Path = Field(default_factory=lambda: Path("var/traces"))
    LOG_LEVEL: str = "INFO"
    MCP_TRANSPORT: str = "stdio"
    MCP_SERVER_NAME: str = "notalink"
    SECRET_KEY: str = "dev"

    def ensure_dirs(self) -> None:
        self.VAR_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.TRACES_DIR.mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "notes").mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "links").mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "index").mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "graph").mkdir(parents=True, exist_ok=True)

_settings: Optional[Settings] = None
def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings
