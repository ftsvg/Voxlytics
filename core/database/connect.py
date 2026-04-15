import os
import pymysql
import functools
from dotenv import load_dotenv
from pymysql.cursors import Cursor

load_dotenv()


def db_connect():
    return pymysql.connect(
        host=os.environ.get("DBENDPOINT"),
        port=int(os.environ.get("DBPORT")),
        user=os.environ.get("DBUSER"),
        password=os.environ.get("DBPASS"),
        database=os.environ.get("DBNAME"),
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )


def ensure_cursor(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cursor: Cursor | None = kwargs.get("cursor")
        if cursor:
            return func(*args, **kwargs)

        with db_connect() as conn:
            cursor = conn.cursor()
            kwargs["cursor"] = cursor
            return func(*args, **kwargs)

    return wrapper


def async_ensure_cursor(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        cursor: Cursor | None = kwargs.get('cursor')
        if cursor:
            return await func(*args, **kwargs)

        with db_connect() as conn:
            cursor = conn.cursor()
            kwargs['cursor'] = cursor
            return await func(*args, **kwargs)

    return wrapper