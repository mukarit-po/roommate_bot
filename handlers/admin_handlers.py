"""
handlers/admin_handlers.py — In-bot Admin Panel with full navigation and pagination.
All operations are protected by admin authorization check.
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from constants import (
    CB_ADMIN_BACK, CB_ADMIN_EXPENSES, CB_ADMIN_GROUPS,
    CB_ADMIN_STATS, CB_ADMIN_USERS, CB_EXPENSE_DELETE,
    CB_EXPENSE_DELETE_CONFIRM, CB_EXPENSE_VIEW, CB_GROUP_VIEW,
    CB_PAGE, CB_USER_VIEW, CMD_ADMIN, MSG_UNAUTHORIZED,
)
from database import get_session
from keyboards.admin_keyboards import (
    admin_main_menu, back_to_main,
    expense_delete_confirm_keyboard, expense_detail_keyboard,
    expenses_list_keyboard, group_detail_keyboard,
    groups_list_keyboard, user_detail_keyboard, users_list_keyboard,
)
from repositories import ExpenseRepository, GroupRepository, UserRepository
from services.balance_service import format_amount
from states import AdminMenuStates

logger = logging.getLogger(__name__)
router = Router()

PAGE_SIZE = settings.page_size


# ── Auth Guard ─────────────────────────────────────────────────────────────────

def is_admin(telegram_id: int) -> bool:
    return telegram_id == settings.admin_chat_id


# ── /admin ─────────────────────────────────────────────────────────────────────

@router.message(Command(CMD_ADMIN))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer(MSG_UNAUTHORIZED)
        return

    await state.set_state(AdminMenuStates.MAIN)
    await message.answer(
        "🔐 *Admin Panel*\n\nSelect a section to manage:",
        parse_mode="Markdown",
        reply_markup=admin_main_menu(),
    )


# ── Back to Main ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == CB_ADMIN_BACK)
async def admin_back(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return
    await state.set_state(AdminMenuStates.MAIN)
    await callback.message.edit_text(
        "🔐 *Admin Panel*\n\nSelect a section to manage:",
        parse_mode="Markdown",
        reply_markup=admin_main_menu(),
    )
    await callback.answer()


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == CB_ADMIN_STATS)
async def admin_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    async with get_session() as session:
        user_repo = UserRepository(session)
        group_repo = GroupRepository(session)
        expense_repo = ExpenseRepository(session)

        total_users = await user_repo.count()
        total_groups = await group_repo.count()
        total_expenses = await expense_repo.count()
        total_money = await expense_repo.total_amount()

    await callback.message.edit_text(
        "📊 *System Statistics*\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"🏠 Total Groups: `{total_groups}`\n"
        f"💸 Total Expenses: `{total_expenses}`\n"
        f"💰 Total Money Tracked: `{format_amount(total_money)}`",
        parse_mode="Markdown",
        reply_markup=back_to_main(),
    )
    await callback.answer()


# ── Users List ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_ADMIN_USERS}:"))
async def admin_users_list(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    page = int(callback.data.split(":")[-1])

    async with get_session() as session:
        user_repo = UserRepository(session)
        users = await user_repo.list_paginated(page, PAGE_SIZE)
        total = await user_repo.count()

    if not users:
        await callback.message.edit_text("👤 No users found.", reply_markup=back_to_main())
        await callback.answer()
        return

    await state.set_state(AdminMenuStates.VIEW_USERS)
    await callback.message.edit_text(
        f"👥 *Users* (Page {page + 1})",
        parse_mode="Markdown",
        reply_markup=users_list_keyboard(users, page, total, PAGE_SIZE),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_USER_VIEW))
async def admin_user_detail(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    user_id = int(callback.data.removeprefix(CB_USER_VIEW))

    async with get_session() as session:
        user_repo = UserRepository(session)
        expense_repo = ExpenseRepository(session)
        user = await user_repo.get_by_id(user_id)

    if user is None:
        await callback.answer("User not found.", show_alert=True)
        return

    username_text = f"@{user.username}" if user.username else "N/A"
    joined = user.created_at.strftime("%Y-%m-%d")

    await callback.message.edit_text(
        f"👤 *User Details*\n\n"
        f"*Name:* {user.name}\n"
        f"*Username:* {username_text}\n"
        f"*Telegram ID:* `{user.telegram_id}`\n"
        f"*Joined:* {joined}\n"
        f"*Active:* {'✅' if user.is_active else '❌'}",
        parse_mode="Markdown",
        reply_markup=user_detail_keyboard(),
    )
    await callback.answer()


# ── Groups List ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_ADMIN_GROUPS}:"))
async def admin_groups_list(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    page = int(callback.data.split(":")[-1])

    async with get_session() as session:
        group_repo = GroupRepository(session)
        groups = await group_repo.list_paginated(page, PAGE_SIZE)
        total = await group_repo.count()

    if not groups:
        await callback.message.edit_text("🏠 No groups found.", reply_markup=back_to_main())
        await callback.answer()
        return

    await state.set_state(AdminMenuStates.VIEW_GROUPS)
    await callback.message.edit_text(
        f"🏠 *Groups* (Page {page + 1})",
        parse_mode="Markdown",
        reply_markup=groups_list_keyboard(groups, page, total, PAGE_SIZE),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_GROUP_VIEW))
async def admin_group_detail(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    group_id = int(callback.data.removeprefix(CB_GROUP_VIEW))

    async with get_session() as session:
        group_repo = GroupRepository(session)
        expense_repo = ExpenseRepository(session)
        group = await group_repo.get_by_id(group_id)
        expense_count = len(await expense_repo.list_by_group(group_id, limit=9999))

    if group is None:
        await callback.answer("Group not found.", show_alert=True)
        return

    members_text = "\n".join(f"• {m.user.name}" for m in group.members)
    created = group.created_at.strftime("%Y-%m-%d")

    await callback.message.edit_text(
        f"🏠 *Group: {group.name}*\n\n"
        f"*Members ({len(group.members)}):*\n{members_text}\n\n"
        f"*Expenses:* {expense_count}\n"
        f"*Created:* {created}",
        parse_mode="Markdown",
        reply_markup=group_detail_keyboard(),
    )
    await callback.answer()


# ── Expenses List ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_ADMIN_EXPENSES}:"))
async def admin_expenses_list(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    page = int(callback.data.split(":")[-1])

    async with get_session() as session:
        expense_repo = ExpenseRepository(session)
        expenses = await expense_repo.list_all_paginated(page, PAGE_SIZE)
        total = await expense_repo.count()

    if not expenses:
        await callback.message.edit_text("💸 No expenses found.", reply_markup=back_to_main())
        await callback.answer()
        return

    await state.set_state(AdminMenuStates.VIEW_EXPENSES)
    await callback.message.edit_text(
        f"💸 *Expenses* (Page {page + 1} of {max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)})",
        parse_mode="Markdown",
        reply_markup=expenses_list_keyboard(expenses, page, total, PAGE_SIZE),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_EXPENSE_VIEW))
async def admin_expense_detail(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    # Avoid collision with delete callbacks
    raw = callback.data.removeprefix(CB_EXPENSE_VIEW)
    if not raw.isdigit():
        return

    expense_id = int(raw)

    async with get_session() as session:
        expense_repo = ExpenseRepository(session)
        expense = await expense_repo.get_by_id(expense_id)

    if expense is None:
        await callback.answer("Expense not found.", show_alert=True)
        return

    participants_text = "\n".join(
        f"• {p.user.name}: `{format_amount(p.share_amount)}`"
        for p in expense.participants
    )
    created = expense.created_at.strftime("%Y-%m-%d %H:%M")

    await callback.message.edit_text(
        f"💸 *Expense #{expense.id}*\n\n"
        f"*Description:* {expense.description}\n"
        f"*Amount:* `{format_amount(expense.amount)}`\n"
        f"*Paid by:* {expense.payer.name}\n"
        f"*Group:* {expense.group.name}\n"
        f"*Date:* {created}\n\n"
        f"*Participants:*\n{participants_text}",
        parse_mode="Markdown",
        reply_markup=expense_detail_keyboard(expense.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_EXPENSE_DELETE))
async def admin_expense_delete_prompt(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    # Strip prefix carefully — avoid matching delconfirm
    raw = callback.data.removeprefix(CB_EXPENSE_DELETE)
    if not raw.isdigit():
        return

    expense_id = int(raw)

    await callback.message.edit_text(
        f"⚠️ *Are you sure you want to delete expense #{expense_id}?*\n\n"
        "This will soft-delete it and it won't appear in balances.",
        parse_mode="Markdown",
        reply_markup=expense_delete_confirm_keyboard(expense_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CB_EXPENSE_DELETE_CONFIRM))
async def admin_expense_delete_confirm(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    expense_id = int(callback.data.removeprefix(CB_EXPENSE_DELETE_CONFIRM))

    async with get_session() as session:
        expense_repo = ExpenseRepository(session)
        success = await expense_repo.soft_delete(expense_id)

    if success:
        await callback.message.edit_text(
            f"✅ Expense #{expense_id} has been deleted.",
            reply_markup=back_to_main(),
        )
        await callback.answer("Deleted!", show_alert=True)
    else:
        await callback.answer("Expense not found.", show_alert=True)


# ── Pagination Dispatcher ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(CB_PAGE))
async def admin_pagination(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_UNAUTHORIZED, show_alert=True)
        return

    # Format: admin:page:<section>:<page_num>
    parts = callback.data.removeprefix(CB_PAGE).split(":")
    section = parts[0]
    page = int(parts[1])

    # Route to appropriate list handler by faking callback data
    if section == "users":
        callback.data = f"{CB_ADMIN_USERS}:{page}"
        await admin_users_list(callback, state)
    elif section == "groups":
        callback.data = f"{CB_ADMIN_GROUPS}:{page}"
        await admin_groups_list(callback, state)
    elif section == "expenses":
        callback.data = f"{CB_ADMIN_EXPENSES}:{page}"
        await admin_expenses_list(callback, state)


# ── Noop (page counter button) ─────────────────────────────────────────────────

@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    await callback.answer()
