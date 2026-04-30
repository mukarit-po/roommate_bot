"""
repositories/expense_repo.py — Data access layer for Expense model.
"""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Expense, ExpenseParticipant, Settlement, User


class ExpenseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        group_id: int,
        payer_id: int,
        amount: float,
        description: str,
        participant_ids: List[int],
    ) -> Expense:
        share = round(amount / len(participant_ids), 2)
        expense = Expense(
            group_id=group_id,
            payer_id=payer_id,
            amount=amount,
            description=description,
        )
        self.session.add(expense)
        await self.session.flush()

        for uid in participant_ids:
            participant = ExpenseParticipant(
                expense_id=expense.id,
                user_id=uid,
                share_amount=share,
            )
            self.session.add(participant)

        await self.session.flush()
        await self.session.refresh(expense)
        return expense

    async def get_by_id(self, expense_id: int) -> Optional[Expense]:
        result = await self.session.execute(
            select(Expense)
            .where(Expense.id == expense_id, Expense.is_deleted == False)
            .options(
                selectinload(Expense.payer),
                selectinload(Expense.participants).selectinload(ExpenseParticipant.user),
                selectinload(Expense.group),
            )
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, expense_id: int) -> bool:
        expense = await self.get_by_id(expense_id)
        if expense is None:
            return False
        expense.is_deleted = True
        return True

    async def list_by_group(self, group_id: int, limit: int = 10) -> List[Expense]:
        result = await self.session.execute(
            select(Expense)
            .where(Expense.group_id == group_id, Expense.is_deleted == False)
            .options(
                selectinload(Expense.payer),
                selectinload(Expense.participants).selectinload(ExpenseParticipant.user),
            )
            .order_by(Expense.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all_paginated(self, page: int, page_size: int) -> List[Expense]:
        offset = page * page_size
        result = await self.session.execute(
            select(Expense)
            .where(Expense.is_deleted == False)
            .options(
                selectinload(Expense.payer),
                selectinload(Expense.participants).selectinload(ExpenseParticipant.user),
                selectinload(Expense.group),
            )
            .order_by(Expense.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).where(Expense.is_deleted == False).select_from(Expense)
        )
        return result.scalar_one()

    async def total_amount(self) -> float:
        result = await self.session.execute(
            select(func.sum(Expense.amount)).where(Expense.is_deleted == False)
        )
        return result.scalar_one() or 0.0

    async def get_group_participants(self, group_id: int) -> List[ExpenseParticipant]:
        result = await self.session.execute(
            select(ExpenseParticipant)
            .join(Expense, Expense.id == ExpenseParticipant.expense_id)
            .where(Expense.group_id == group_id, Expense.is_deleted == False)
            .options(selectinload(ExpenseParticipant.user), selectinload(ExpenseParticipant.expense))
        )
        return list(result.scalars().all())


class SettlementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, group_id: int, debtor_id: int, creditor_id: int, amount: float
    ) -> Settlement:
        settlement = Settlement(
            group_id=group_id,
            debtor_id=debtor_id,
            creditor_id=creditor_id,
            amount=amount,
        )
        self.session.add(settlement)
        await self.session.flush()
        return settlement

    async def get_group_settlements(self, group_id: int) -> List[Settlement]:
        result = await self.session.execute(
            select(Settlement).where(Settlement.group_id == group_id)
        )
        return list(result.scalars().all())
