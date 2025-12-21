import os
import aiosqlite
import asyncpg
import logging
from datetime import datetime

# Настройки
DB_NAME = "bot_database.db"
DATABASE_URL = os.getenv("DATABASE_URL") # Railway предоставляет эту переменную для Postgres

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.type = "postgres" if DATABASE_URL else "sqlite"
        self.pool = None

    async def connect(self):
        if self.type == "postgres":
            try:
                self.pool = await asyncpg.create_pool(DATABASE_URL)
                logger.info("Connected to PostgreSQL")
                await self.init_postgres()
            except Exception as e:
                logger.error(f"Postgres connection failed: {e}. Falling back to SQLite.")
                self.type = "sqlite"
        
        if self.type == "sqlite":
            logger.info("Using SQLite")
            await self.init_sqlite()

    async def init_postgres(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    selected_model TEXT DEFAULT 'gemini-2.5-flash',
                    system_instruction TEXT DEFAULT 'Ты полезный и умный ассистент.',
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 4096,
                    use_tools BOOLEAN DEFAULT FALSE,
                    stream_response BOOLEAN DEFAULT TRUE
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS message_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    role TEXT,
                    content TEXT,
                    has_media BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    async def init_sqlite(self):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    selected_model TEXT DEFAULT 'gemini-2.5-flash',
                    system_instruction TEXT DEFAULT 'Ты полезный и умный ассистент.',
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 4096,
                    use_tools BOOLEAN DEFAULT 0,
                    stream_response BOOLEAN DEFAULT 1
                )
            """)
            # Migrations for sqlite
            try:
                await db.execute("ALTER TABLE users ADD COLUMN stream_response BOOLEAN DEFAULT 1")
            except: pass

            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT,
                    content TEXT,
                    has_media BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            await db.commit()

    async def get_user_settings(self, user_id: int):
        defaults = {
            "user_id": user_id,
            "selected_model": "gemini-2.5-flash",
            "system_instruction": "Ты полезный и умный ассистент.",
            "temperature": 0.7,
            "max_tokens": 4096,
            "use_tools": False,
            "stream_response": True
        }

        if self.type == "postgres":
            if not self.pool: await self.connect()
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                if row: return dict(row)
                await conn.execute("INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)
                return defaults
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row: return dict(row)
                    await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                    await db.commit()
                    return defaults

    async def update_user_setting(self, user_id: int, setting: str, value):
        if self.type == "postgres":
            if not self.pool: await self.connect()
            async with self.pool.acquire() as conn:
                # Postgres boolean handling
                if setting in ['use_tools', 'stream_response']:
                    value = bool(value)
                await conn.execute(f"UPDATE users SET {setting} = $1 WHERE user_id = $2", value, user_id)
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute(f"UPDATE users SET {setting} = ? WHERE user_id = ?", (value, user_id))
                await db.commit()

    async def save_message(self, user_id: int, role: str, content: str, has_media: bool = False):
        if self.type == "postgres":
            if not self.pool: await self.connect()
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO message_history (user_id, role, content, has_media) VALUES ($1, $2, $3, $4)",
                    user_id, role, content, has_media
                )
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute(
                    "INSERT INTO message_history (user_id, role, content, has_media) VALUES (?, ?, ?, ?)",
                    (user_id, role, content, has_media)
                )
                await db.commit()

    async def get_chat_history(self, user_id: int, limit: int = 20):
        if self.type == "postgres":
            if not self.pool: await self.connect()
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT role, content FROM message_history WHERE user_id = $1 ORDER BY id DESC LIMIT $2",
                    user_id, limit
                )
                return [dict(row) for row in reversed(rows)]
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT role, content FROM message_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                    (user_id, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in reversed(rows)]

    async def clear_history(self, user_id: int):
        if self.type == "postgres":
            if not self.pool: await self.connect()
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM message_history WHERE user_id = $1", user_id)
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute("DELETE FROM message_history WHERE user_id = ?", (user_id,))
                await db.commit()

# Singleton instance
db_instance = Database()

# Wrapper functions for compatibility
async def init_db():
    await db_instance.connect()

async def get_user_settings(user_id):
    return await db_instance.get_user_settings(user_id)

async def update_user_setting(user_id, setting, value):
    await db_instance.update_user_setting(user_id, setting, value)

async def save_message(user_id, role, content, has_media=False):
    await db_instance.save_message(user_id, role, content, has_media)

async def get_chat_history(user_id, limit=20):
    return await db_instance.get_chat_history(user_id, limit)

async def clear_history(user_id):
    await db_instance.clear_history(user_id)
