import os
import aiosqlite
import asyncpg
import logging
from datetime import datetime

# Database setup
DB_NAME = "bot_database.db"
DATABASE_URL = os.getenv("DATABASE_URL") # Railway Postgres URL

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
                    selected_model TEXT DEFAULT 'gemini-1.5-flash',
                    system_instruction TEXT DEFAULT 'Ты — умный и полезный ассистент.',
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 2048,
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
                    selected_model TEXT DEFAULT 'gemini-1.5-flash',
                    system_instruction TEXT DEFAULT 'Ты — умный и полезный ассистент.',
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 2048,
                    use_tools BOOLEAN DEFAULT FALSE,
                    stream_response BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Check for missing columns in existing table (Migration)
            try:
                await db.execute("ALTER TABLE users ADD COLUMN stream_response BOOLEAN DEFAULT 1")
            except:
                pass

            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(user_id),
                    role TEXT,
                    content TEXT,
                    has_media BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def get_user_settings(self, user_id):
        if self.type == "postgres":
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                if row: return dict(row)
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row: return dict(row)
        
        # Default settings if user not found
        return {
            "user_id": user_id,
            "selected_model": "gemini-1.5-flash-latest",
            "system_instruction": "Ты — умный и полезный ассистент.",
            "temperature": 0.7,
            "max_tokens": 2048,
            "use_tools": False,
            "stream_response": True
        }

    async def update_user_setting(self, user_id, setting, value):
        # Whitelist allowed settings
        allowed_settings = ['username', 'selected_model', 'system_instruction', 'temperature', 'max_tokens', 'use_tools', 'stream_response']
        if setting not in allowed_settings:
            return

        if self.type == "postgres":
            async with self.pool.acquire() as conn:
                # Upsert logic
                await conn.execute(f"""
                    INSERT INTO users (user_id, {setting}) VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE SET {setting} = $2
                """, user_id, value)
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute(f"INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
                await db.execute(f"UPDATE users SET {setting} = ? WHERE user_id = ?", (value, user_id))
                await db.commit()

    async def save_message(self, user_id, role, content, has_media=False):
        if self.type == "postgres":
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO message_history (user_id, role, content, has_media) 
                    VALUES ($1, $2, $3, $4)
                """, user_id, role, content, has_media)
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute("""
                    INSERT INTO message_history (user_id, role, content, has_media) 
                    VALUES (?, ?, ?, ?)
                """, (user_id, role, content, int(has_media)))
                await db.commit()

    async def get_chat_history(self, user_id, limit=10):
        if self.type == "postgres":
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT role, content FROM message_history 
                    WHERE user_id = $1 ORDER BY timestamp DESC LIMIT $2
                """, user_id, limit)
                return [dict(r) for r in reversed(rows)]
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT role, content FROM message_history 
                    WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
                """, (user_id, limit)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in reversed(rows)]

    async def clear_chat_history(self, user_id):
        if self.type == "postgres":
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM message_history WHERE user_id = $1", user_id)
        else:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute("DELETE FROM message_history WHERE user_id = ?", (user_id,))
                await db.commit()

db = Database()

# Export functions for compatibility
async def init_db():
    await db.connect()

async def get_user_settings(user_id):
    return await db.get_user_settings(user_id)

async def update_user_setting(user_id, setting, value):
    await db.update_user_setting(user_id, setting, value)

async def save_message(user_id, role, content, has_media=False):
    await db.save_message(user_id, role, content, has_media)

async def get_chat_history(user_id, limit=10):
    return await db.get_chat_history(user_id, limit)

async def clear_chat_history(user_id):
    await db.clear_chat_history(user_id)
