"""
services/expense_service.py — High-level operations for expense management.
"""

from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from models import Expense, Group, Settlement, User
from repositories import ExpenseRepository, GroupRepository, SettlementRepository, UserRepository
from services.balance_service import DebtEntry, compute_balances, optimize_debts


class ExpenseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.expense_repo = ExpenseRepository(session)
        self.group_repo = GroupRepository(session)
        self.settlement_repo = SettlementRepository(session)
        self.user_repo = UserRepository(session)

    async def add_expense(
        self,
        telegram_id: int,
        amount: float,
        description: str,
        participant_ids: Optional[List[int]] = None,
    ) -> Tuple[Expense, Group]:
        """Add an expense for the user's group."""
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            raise LookupError("User not found.")

        group = await self.group_repo.get_user_group(user.id)
        if group is None:
            raise LookupError("You are not in any group.")

        if participant_ids is None:
            # Default: all group members
            members = await self.group_repo.get_members(group.id)
            participant_ids = [m.id for m in members]

        if not participant_ids:
            raise ValueError("No participants selected.")

        expense = await self.expense_repo.create(
            group_id=group.id,
            payer_id=user.id,
            amount=amount,
            description=description,
            participant_ids=participant_ids,
        )
        return expense, group

    async def get_group_balances(self, telegram_id: int) -> Tuple[List[DebtEntry], User]:
        """Compute optimized debt list for the user's group."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            raise LookupError("User not found.")

        group = await self.group_repo.get_user_group(user.id)
        if group is None:
            raise LookupError("You are not in any group.")

        expenses = await self.expense_repo.list_by_group(group.id, limit=1000)
        participants_all = await self.expense_repo.get_group_participants(group.id)
        members = await self.group_repo.get_members(group.id)

        # Subtract settled amounts
        settlements = await self.settlement_repo.get_group_settlements(group.id)

        users_by_id = {m.id: m for m in members}
        balances = compute_balances(participants_all, expenses, users_by_id)

        # Apply settlements
        for s in settlements:
            balances[s.creditor_id] = balances.get(s.creditor_id, 0) - s.amount
            balances[s.debtor_id] = balances.get(s.debtor_id, 0) + s.amount

        # Only include users that are in the group
        balances = {uid: bal for uid, bal in balances.items() if uid in users_by_id}
        transactions = optimize_debts(balances, users_by_id)
        return transactions, user

    async def settle_debt(
        self,
        telegram_id: int,
        creditor_user_id: int,
    ) -> float:
        """Settle all debts the current user owes to a specific creditor."""
        transactions, current_user = await self.get_group_balances(telegram_id)

        amount_to_settle = 0.0
        for t in transactions:
            if t.debtor.id == current_user.id and t.creditor.id == creditor_user_id:
                amount_to_settle += t.amount

        if amount_to_settle == 0:
            raise ValueError("No debt found to settle.")

        group = await self.group_repo.get_user_group(current_user.id)
        await self.settlement_repo.create(
            group_id=group.id,
            debtor_id=current_user.id,
            creditor_id=creditor_user_id,
            amount=amount_to_settle,
        )
        return amount_to_settle

    async def pay_user(
        self,
        telegram_id: int,
        amount: float,
        recipient_username: str,
    ) -> Tuple[Settlement, User, User]:
        """Record a direct payment from current user to another user by username."""
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        current_user = await self.user_repo.get_by_telegram_id(telegram_id)
        if current_user is None:
            raise LookupError("User not found.")

        group = await self.group_repo.get_user_group(current_user.id)
        if group is None:
            raise LookupError("You are not in any group.")

        # Find recipient by username (without @)
        username = recipient_username.lstrip('@')
        recipient = await self.user_repo.get_by_username(username)
        if recipient is None:
            raise LookupError(f"User @{username} not found.")

        # Check if recipient is in the same group
        is_member = await self.group_repo.is_member(group.id, recipient.id)
        if not is_member:
            raise LookupError(f"@{username} is not in your group.")

        if current_user.id == recipient.id:
            raise ValueError("You cannot pay yourself.")

        # Create settlement record
        settlement = await self.settlement_repo.create(
            group_id=group.id,
            debtor_id=current_user.id,  # payer becomes debtor (owes less)
            creditor_id=recipient.id,   # recipient becomes creditor (is owed more)
            amount=amount,
        )

        return settlement, current_user, recipient

    async def get_group_history(self, telegram_id: int, limit: int = 10) -> Tuple[List[Expense], Group]:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            raise LookupError("User not found.")
        group = await self.group_repo.get_user_group(user.id)
        if group is None:
            raise LookupError("You are not in any group.")
        expenses = await self.expense_repo.list_by_group(group.id, limit=limit)
        return expenses, group
