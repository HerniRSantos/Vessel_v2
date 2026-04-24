import os
from urllib.parse import quote_plus
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "database": os.getenv("PG_DB", "vessels_db"),
    "user": os.getenv("PG_USER", "vessel_user"),
    "password": os.getenv("PG_PASSWORD", "vessel_pass_2026"),
}

PG_URL = (
    f"postgresql://{DB_CONFIG['user']}:{quote_plus(DB_CONFIG['password'])}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

engine = create_engine(PG_URL, poolclass=NullPool, echo=False)


@contextmanager
def get_db_connection():
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


def get_engine():
    return engine


def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DB error: {e}")
        return False


if __name__ == "__main__":
    print("Testing database connection...")
    if test_connection():
        print("Database connection OK")
    else:
        print("Database connection FAILED")