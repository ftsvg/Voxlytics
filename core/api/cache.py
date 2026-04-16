import json
import redis
from cachetools import TTLCache
from typing import Any, Optional

from core import logger


class Cache:
    def __init__(
        self,
        redis_host: str,
        redis_port: int,
        password: str
    ):
        self.memory = TTLCache(maxsize=2000, ttl=300)
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=password,
            decode_responses=True
        )

        try:
            self.redis.ping()
            logger.info("Redis connected!")
        except Exception:
            logger.warning("Redis not connected.")


    def make_key(self, endpoint: str, params: dict) -> str:
        return f"{endpoint}:{json.dumps(params, sort_keys=True)}"


    def get(self, key: str) -> Optional[Any]:
        if key in self.memory:
            return self.memory[key]

        try:
            value = self.redis.get(key)
        except Exception:
            logger.error(f"CACHE ERROR (redis get): {key}")
            return None

        if value is None:
            logger.debug(f"CACHE MISS (redis): {key}")
            return None

        try:
            data = json.loads(value)
        except Exception:
            logger.error(f"CACHE ERROR (decode): {key}")
            return None

        self.memory[key] = data
        return data


    def set(self, key: str, value: Any, ttl: int = 300):
        self.memory[key] = value

        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            logger.error(f"CACHE ERROR (redis set): {key}")


    def delete(self, key: str):
        self.memory.pop(key, None)

        try:
            self.redis.delete(key)
        except Exception:
            logger.error(f"CACHE ERROR (redis delete): {key}")