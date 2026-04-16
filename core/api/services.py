import os
from dotenv import load_dotenv

from core.api import Cache, VoxylAPI, SkinAPI

load_dotenv()

cache = Cache(
    redis_host=os.environ.get("REDIS_HOST"),
    redis_port=int(os.environ.get("REDIS_PORT")),
    password=os.environ.get("REDIS_PASSWORD")
)

API = VoxylAPI(cache=cache)
SKINS_API = SkinAPI(cache=cache)