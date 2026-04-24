from requests_cache import CachedSession

mojang_session = CachedSession(cache_name=f".cache/mojang", expire_after=60)

MAIN_COLOR: int = 0x5555FF
COLOR_RED: int = 0xFF7276
COLOR_GREEN: int = 0x90EE90