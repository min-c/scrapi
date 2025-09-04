import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    user_agent: str = os.getenv("SCRAPER_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    timeout: float = float(os.getenv("SCRAPER_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    backoff_factor: float = float(os.getenv("SCRAPER_BACKOFF", "0.5"))
    rate_per_sec: float = float(os.getenv("SCRAPER_RATE_PER_SEC", "1.0"))  # 1 request/sec default

settings = Settings()
