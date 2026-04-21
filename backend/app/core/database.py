from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Lightweight, idempotent migrations for columns added after initial schema.
        # (Using ALTER TABLE ... ADD COLUMN IF NOT EXISTS — Postgres 9.6+.)
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE"
        ))

        # Auto-promote the configured admin email, if set.
        if settings.ADMIN_EMAIL:
            await conn.execute(
                text("UPDATE users SET is_admin = TRUE WHERE email = :email"),
                {"email": settings.ADMIN_EMAIL},
            )
