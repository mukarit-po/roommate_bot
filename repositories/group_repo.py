"""
repositories/group_repo.py — Data access layer for Group model.
"""

from typing import Optional, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Group, GroupMember, User


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, created_by: int) -> Group:
        group = Group(name=name, created_by=created_by)
        self.session.add(group)
        await self.session.flush()
        await self.session.refresh(group)
        return group

    async def get_by_id(self, group_id: int) -> Optional[Group]:
        result = await self.session.execute(
            select(Group)
            .where(Group.id == group_id, Group.is_active == True)
            .options(selectinload(Group.members).selectinload(GroupMember.user))
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Group]:
        result = await self.session.execute(
            select(Group)
            .where(Group.is_active == True)
            .options(selectinload(Group.members).selectinload(GroupMember.user))
            .order_by(Group.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_paginated(self, page: int, page_size: int) -> List[Group]:
        offset = page * page_size
        result = await self.session.execute(
            select(Group)
            .where(Group.is_active == True)
            .options(selectinload(Group.members).selectinload(GroupMember.user))
            .order_by(Group.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).where(Group.is_active == True).select_from(Group)
        )
        return result.scalar_one()

    async def add_member(self, group_id: int, user_id: int) -> GroupMember:
        member = GroupMember(group_id=group_id, user_id=user_id)
        self.session.add(member)
        await self.session.flush()
        return member

    async def is_member(self, group_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_user_group(self, user_id: int) -> Optional[Group]:
        """Get the first active group a user belongs to."""
        result = await self.session.execute(
            select(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .where(GroupMember.user_id == user_id, Group.is_active == True)
            .options(selectinload(Group.members).selectinload(GroupMember.user))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_members(self, group_id: int) -> List[User]:
        result = await self.session.execute(
            select(User)
            .join(GroupMember, GroupMember.user_id == User.id)
            .where(GroupMember.group_id == group_id, User.is_active == True)
        )
        return list(result.scalars().all())
