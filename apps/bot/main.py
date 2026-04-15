import os
from dotenv import load_dotenv; load_dotenv()

from .helpers import Client


if __name__ == "__main__":
    Client().run(os.environ.get("TOKEN"))