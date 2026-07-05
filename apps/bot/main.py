import os
from dotenv import load_dotenv

from .helpers import Client

load_dotenv()

if __name__ == "__main__":
    Client().run(os.environ.get("TOKEN"))