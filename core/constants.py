from requests_cache import CachedSession

mojang_session = CachedSession(cache_name=f".cache/mojang", expire_after=60)
