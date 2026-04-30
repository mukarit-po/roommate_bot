"""
repositories/user_repo.py — Data access layer for User model.
"""

from typing import Optional, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int, name: str, username: Optional[str] = None) -> User:
        user = User(telegram_id=telegram_id, name=name, username=username)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_or_create(self, telegram_id: int, name: str, username: Optional[str] = None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.create(telegram_id, name, username)
        else:
            # Update name if changed
            user.name = name
            user.username = username
        return user

    async def list_paginated(self, page: int, page_size: int) -> List[User]:
        offset = page * page_size
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).where(User.is_active == True).select_from(User)
        )
        return result.scalar_one()
