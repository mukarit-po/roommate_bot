"""
keyboards/user_keyboards.py — Inline keyboards for regular user flows.
"""

from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import CB_JOIN_GROUP, CB_PARTICIPANT, CB_PARTICIPANTS_DONE, CB_SETTLE_DEBT, CB_SETTLE_CONFIRM
from models import Group, User
from services.balance_service import DebtEntry, format_amount


def groups_list_keyboard(groups: List[Group]) -> InlineKeyboardMarkup:
    """Display available groups to join."""
    builder = InlineKeyboardBuilder()
    for group in groups:
        member_count = len(group.members)
        builder.button(
            text=f"🏠 {group.name} ({member_count} members)",
            callback_data=f"{CB_JOIN_GROUP}{group.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def participants_keyboard(
    members: List[User],
    selected_ids: List[int],
    payer_id: int,
) -> InlineKeyboardMarkup:
    """Toggle-style keyboard for selecting expense participants."""
    builder = InlineKeyboardBuilder()
    for member in members:
        is_selected = member.id in selected_ids
        checkmark = "✅" if is_selected else "☑️"
        is_payer = " (payer)" if member.id == payer_id else ""
        builder.button(
            text=f"{checkmark} {member.name}{is_payer}",
            callback_data=f"{CB_PARTICIPANT}{member.id}",
        )
    builder.button(text="✔️ Done", callback_data=CB_PARTICIPANTS_DONE)
    builder.adjust(1)
    return builder.as_markup()


def settle_keyboard(transactions: List[DebtEntry], current_user_id: int) -> InlineKeyboardMarkup:
    """Show who the current user owes and allow settling."""
    builder = InlineKeyboardBuilder()
    my_debts = [t for t in transactions if t.debtor.id == current_user_id]
    for t in my_debts:
        builder.button(
            text=f"💳 Pay {t.creditor.name} {format_amount(t.amount)}",
            callback_data=f"{CB_SETTLE_DEBT}{t.creditor.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def settle_confirm_keyboard(creditor_id: int, amount: float, creditor_name: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ Confirm — pay {format_amount(amount)} to {creditor_name}",
        callback_data=f"{CB_SETTLE_CONFIRM}{creditor_id}",
    )
    builder.button(text="❌ Cancel", callback_data="settle:cancel")
    builder.adjust(1)
    return builder.as_markup()
