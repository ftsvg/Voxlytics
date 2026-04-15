import json
import time
from typing import Any, Optional
from contextlib import contextmanager

from core.database import db_connect


class MySQLCache:
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl

    @contextmanager
    def cursor(self):
        conn = db_connect()
        try:
            cur = conn.cursor()
            yield cur
            conn.commit()
        finally:
            conn.close()


    def make_key(self, endpoint: str, params: dict) -> str:
        return f"{endpoint}:{json.dumps(params, sort_keys=True)}"


    def get(self, key: str) -> Optional[Any]:
        with self.cursor() as cur:
            cur.execute(
                "SELECT response, expires_at FROM api_cache WHERE cache_key=%s", (key,)
            )
            row = cur.fetchone()

            if not row:
                return None

            response, expires_at = row
            now = int(time.time())

            try:
                expires_at = int(expires_at)
            except:
                return None

            if now > expires_at:
                self.delete(key)
                return None

            return json.loads(response)


    def set(self, key: str, endpoint: str, data: Any, ttl: int | None = None):
        ttl = ttl or self.default_ttl
        expires_at = int(time.time()) + ttl

        with self.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_cache (cache_key, endpoint, response, expires_at)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    response=VALUES(response),
                    endpoint=VALUES(endpoint),
                    expires_at=VALUES(expires_at),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (key, endpoint, json.dumps(data), expires_at),
            )


    def delete(self, key: str):
        with self.cursor() as cur:
            cur.execute("DELETE FROM api_cache WHERE cache_key=%s", (key,))


    def cleanup(self):
        with self.cursor() as cur:
            cur.execute(
                "DELETE FROM api_cache WHERE expires_at < %s", (int(time.time()),)
            )
