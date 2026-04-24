import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://vessel_user:vessel_pass_2026@localhost:5432/vessels_db"
    )
)

SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

engine = create_engine(
    SYNC_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db_pool():
    conn_str = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.create_pool(
        conn_str,
        min_size=2,
        max_size=10
    )


def init_db():
    """Initialize database with schema"""
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "migrations",
        "postgres_schema.sql"
    )
    
    if os.path.exists(schema_path):
        with engine.connect() as conn:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            for stmt in schema_sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    try:
                        conn.execute(text(stmt))
                    except Exception as e:
                        print(f"Schema statement error: {e}")
            conn.commit()
            print("PostgreSQL schema initialized")
    else:
        print("Schema file not found, using existing database")


def test_connection() -> bool:
    """Test database connectivity"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DB connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing database connection...")
    if test_connection():
        print("Database connection OK")
        init_db()
    else:
        print("Database connection FAILED")