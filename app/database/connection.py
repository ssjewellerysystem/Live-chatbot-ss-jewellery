import asyncpg
import re
from typing import List, Dict, Any, Optional
from app.config import settings

class DatabaseConnectionManager:
    """
    Database Connection Pool Manager utilizing asyncpg.
    Enforces a strict read-only query policy at the execution level.
    """
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def initialize(cls):
        """
        Initializes the connection pool with Neon.
        """
        if cls._pool is None:
            # Parse the DSN to resolve any options if necessary, asyncpg accepts standard postgresql://
            cls._pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=10
            )

    @classmethod
    async def close(cls):
        """
        Closes the connection pool.
        """
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    def validate_query(cls, query: str):
        """
        Validates that the query is strictly a SELECT (read-only) statement.
        Protects against execution-level write attempts.
        """
        # Strip comments
        query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
        query_clean = query_clean.strip().lower()
        
        # Must start with select or with
        if not (query_clean.startswith("select") or query_clean.startswith("with")):
            raise PermissionError("Database query rejected: Only SELECT queries are allowed.")
            
        # Forbidden write words (using word boundaries to avoid false positives on columns like created_at)
        forbidden_keywords = [
            "insert", "update", "delete", "alter", "drop", "truncate", 
            "create", "merge", "replace", "grant", "revoke"
        ]
        for kw in forbidden_keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, query_clean):
                raise PermissionError(f"Database query rejected: Query contains forbidden write keyword '{kw}'.")

    @classmethod
    async def fetch(cls, query: str, *args) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query and returns a list of dictionaries.
        """
        cls.validate_query(query)
        await cls.initialize()
        if cls._pool is None:
            raise RuntimeError("Database pool not initialized.")
        async with cls._pool.acquire() as conn:
            records = await conn.fetch(query, *args)
            return [dict(r) for r in records]

    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Executes a SELECT query and returns the first row as a dictionary, or None.
        """
        cls.validate_query(query)
        await cls.initialize()
        if cls._pool is None:
            raise RuntimeError("Database pool not initialized.")
        async with cls._pool.acquire() as conn:
            record = await conn.fetchrow(query, *args)
            return dict(record) if record else None

    @classmethod
    async def fetchval(cls, query: str, *args) -> Any:
        """
        Executes a SELECT query and returns a single scalar value.
        """
        cls.validate_query(query)
        await cls.initialize()
        if cls._pool is None:
            raise RuntimeError("Database pool not initialized.")
        async with cls._pool.acquire() as conn:
            return await conn.fetchval(query, *args)
