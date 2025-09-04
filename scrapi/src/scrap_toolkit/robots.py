import urllib.robotparser as robotparser
from functools import lru_cache

@lru_cache(maxsize=256)
def can_fetch(robots_url: str, user_agent: str, url: str) -> bool:
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        # Be conservative: if robots can't be read, deny (or choose True if your policy allows)
        return False
    return rp.can_fetch(user_agent, url)
