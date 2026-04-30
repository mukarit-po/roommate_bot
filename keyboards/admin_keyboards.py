"""
keyboards/admin_keyboards.py — Inline keyboards for the admin panel.
"""

from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import (
    CB_ADMIN_BACK, CB_ADMIN_EXPENSES, CB_ADMIN_GROUPS,
    CB_ADMIN_STATS, CB_ADMIN_USERS, CB_EXPENSE_DELETE,
    CB_EXPENSE_DELETE_CONFIRM, CB_EXPENSE_VIEW, CB_GROUP_VIEW,
    CB_PAGE, CB_USER_VIEW,
)
from models import Expense, Group, User
from services.balance_service import format_amount


def admin_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Stats", callback_data=CB_ADMIN_STATS)
    builder.button(text="👥 Users", callback_data=f"{CB_ADMIN_USERS}:0")
    builder.button(text="🏠 Groups", callback_data=f"{CB_ADMIN_GROUPS}:0")
    builder.button(text="💸 Expenses", callback_data=f"{CB_ADMIN_EXPENSES}:0")
    builder.adjust(2)
    return builder.as_markup()


def back_to_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back to Admin Menu", callback_data=CB_ADMIN_BACK)
    return builder.as_markup()


def users_list_keyboard(users: List[User], page: int, total: int, page_size: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        builder.button(
            text=f"👤 {user.name} (ID: {user.telegram_id})",
            callback_data=f"{CB_USER_VIEW}{user.id}",
        )
    builder.adjust(1)
    _add_pagination_buttons(builder, "users", page, total, page_size)
    builder.button(text="🔙 Back", callback_data=CB_ADMIN_BACK)
    builder.adjust(1)
    return builder.as_markup()


def groups_list_keyboard(groups: List[Group], page: int, total: int, page_size: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        member_count = len(group.members)
        builder.button(
            text=f"🏠 {group.name} ({member_count} members)",
            callback_data=f"{CB_GROUP_VIEW}{group.id}",
        )
    builder.adjust(1)
    _add_pagination_buttons(builder, "groups", page, total, page_size)
    builder.button(text="🔙 Back", callback_data=CB_ADMIN_BACK)
    builder.adjust(1)
    return builder.as_markup()


def expenses_list_keyboard(expenses: List[Expense], page: int, total: int, page_size: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for exp in expenses:
        date_str = exp.created_at.strftime("%b %d")
        builder.button(
            text=f"💸 {format_amount(exp.amount)} — {exp.description[:20]} ({date_str})",
            callback_data=f"{CB_EXPENSE_VIEW}{exp.id}",
        )
    builder.adjust(1)
    _add_pagination_buttons(builder, "expenses", page, total, page_size)
    builder.button(text="🔙 Back", callback_data=CB_ADMIN_BACK)
    builder.adjust(1)
    return builder.as_markup()


def expense_detail_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Delete Expense", callback_data=f"{CB_EXPENSE_DELETE}{expense_id}")
    builder.button(text="🔙 Back to List", callback_data=f"{CB_ADMIN_EXPENSES}:0")
    builder.adjust(1)
    return builder.as_markup()


def expense_delete_confirm_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⚠️ Yes, Delete", callback_data=f"{CB_EXPENSE_DELETE_CONFIRM}{expense_id}")
    builder.button(text="❌ Cancel", callback_data=f"{CB_EXPENSE_VIEW}{expense_id}")
    builder.adjust(2)
    return builder.as_markup()


def user_detail_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back to Users", callback_data=f"{CB_ADMIN_USERS}:0")
    return builder.as_markup()


def group_detail_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back to Groups", callback_data=f"{CB_ADMIN_GROUPS}:0")
    return builder.as_markup()


# ── Internal Helper ────────────────────────────────────────────────────────────

def _add_pagination_buttons(
    builder: InlineKeyboardBuilder,
    section: str,
    page: int,
    total: int,
    page_size: int,
) -> None:
    total_pages = max(1, (total + page_size - 1) // page_size)
    nav_pairs = []

    if page > 0:
        nav_pairs.append(("◀️ Prev", f"{CB_PAGE}{section}:{page - 1}"))

    nav_pairs.append((f"{page + 1}/{total_pages}", "noop"))

    if (page + 1) * page_size < total:
        nav_pairs.append(("Next ▶️", f"{CB_PAGE}{section}:{page + 1}"))

    for text, cb in nav_pairs:
        builder.button(text=text, callback_data=cb)
    builder.adjust(len(nav_pairs))
