"""
handlers/user_handlers.py — All regular user command and callback handlers.
"""

import logging
from typing import List

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import (
    CB_JOIN_GROUP, CB_PARTICIPANT, CB_PARTICIPANTS_DONE,
    CB_SETTLE_DEBT, CB_SETTLE_CONFIRM,
    CMD_ADD, CMD_BALANCE, CMD_CREATE_GROUP, CMD_HELP,
    CMD_HISTORY, CMD_JOIN, CMD_SETTLE, CMD_START, CMD_PAY,
    MSG_NOT_IN_GROUP,
)
from database import get_session
from keyboards.user_keyboards import (
    groups_list_keyboard, participants_keyboard,
    settle_confirm_keyboard, settle_keyboard,
)
from repositories import GroupRepository, UserRepository
from services import ExpenseService
from services.balance_service import format_balance_message, format_amount
from states import AddExpenseStates, CreateGroupStates, JoinGroupStates, SettleStates

logger = logging.getLogger(__name__)
router = Router()


# ── /start ─────────────────────────────────────────────────────────────────────

@router.message(Command(CMD_START))
async def cmd_start(message: Message) -> None:
    async with get_session() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            username=message.from_user.username,
        )
    await message.answer(
        f"👋 Welcome, *{user.name}*!\n\n"
        "I'm your roommate expense tracker bot.\n\n"
        "*Commands:*\n"
        "/create\\_group — Create a new group\n"
        "/join — Join an existing group\n"
        "/add — Add an expense (example: `/add 45.50 dinner`)\n"
        "/balance — See who owes what\n"
        "/history — Recent expenses\n"
        "/settle — Settle a debt\n"
        "/pay — Pay someone directly\n"
        "/help — This message",
        parse_mode="Markdown",
    )


# ── /help ──────────────────────────────────────────────────────────────────────

@router.message(Command(CMD_HELP))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "🤖 *Roommate Expense Bot*\n\n"
        "*/create\\_group* — Create a new roommate group\n"
        "*/join* — Browse and join an existing group\n"
        "*/add* — Record a shared expense (example: `/add 45.50 dinner`)\n"
        "*/balance* — View optimized debt summary\n"
        "*/history* — See last 10 expenses\n"
        "*/settle* — Mark your debts as paid\n"
        "*/pay* — Pay someone directly (example: `/pay 50 @username`)",
        parse_mode="Markdown",
    )


# ── /create_group ──────────────────────────────────────────────────────────────

@router.message(Command(CMD_CREATE_GROUP))
async def cmd_create_group(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateGroupStates.WAITING_NAME)
    await message.answer("🏠 What's the name for your new group?")


@router.message(CreateGroupStates.WAITING_NAME)
async def process_group_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("⚠️ Group name cannot be empty. Try again:")
        return

    async with get_session() as session:
        user_repo = UserRepository(session)
        group_repo = GroupRepository(session)

        user = await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            username=message.from_user.username,
        )
        group = await group_repo.create(name=name, created_by=message.from_user.id)
        await group_repo.add_member(group_id=group.id, user_id=user.id)

    await state.clear()
    await message.answer(
        f"✅ Group *{name}* created!\n"
        f"Share this with your roommates: they can join using /join",
        parse_mode="Markdown",
    )


# ── /join ──────────────────────────────────────────────────────────────────────

@router.message(Command(CMD_JOIN))
async def cmd_join(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        group_repo = GroupRepository(session)
        groups = await group_repo.list_all()

    if not groups:
        await message.answer("😔 No groups exist yet. Create one with /create_group!")
        return

    await state.set_state(JoinGroupStates.SELECTING_GROUP)
    await message.answer(
        "🏠 Select a group to join:",
        reply_markup=groups_list_keyboard(groups),
    )


@router.callback_query(JoinGroupStates.SELECTING_GROUP, F.data.startswith(CB_JOIN_GROUP))
async def process_join_group(callback: CallbackQuery, state: FSMContext) -> None:
    group_id = int(callback.data.removeprefix(CB_JOIN_GROUP))

    async with get_session() as session:
        user_repo = UserRepository(session)
        group_repo = GroupRepository(session)

        user = await user_repo.get_or_create(
            telegram_id=callback.from_user.id,
            name=callback.from_user.full_name,
            username=callback.from_user.username,
        )
        group = await group_repo.get_by_id(group_id)

        if group is None:
            await callback.answer("Group not found.", show_alert=True)
            return

        if await group_repo.is_member(group_id=group.id, user_id=user.id):
            await callback.answer("You're already in this group!", show_alert=True)
            await state.clear()
            return

        await group_repo.add_member(group_id=group.id, user_id=user.id)
        group_name = group.name

    await state.clear()
    await callback.message.edit_text(
        f"✅ You joined *{group_name}*!\n\nUse /add to record expenses.",
        parse_mode="Markdown",
    )
    await callback.answer()


# ── /add ───────────────────────────────────────────────────────────────────────

@router.message(Command(CMD_ADD))
async def cmd_add(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    parts = text.split(maxsplit=2)
    amount_arg = None
    description_arg = None

    if len(parts) >= 2:
        amount_arg = parts[1]
    if len(parts) == 3:
        description_arg = parts[2].strip()

    async with get_session() as session:
        user_repo = UserRepository(session)
        group_repo = GroupRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if user is None or not await group_repo.get_user_group(user.id):
            await message.answer(MSG_NOT_IN_GROUP)
            return

    if amount_arg and description_arg:
        try:
            amount = float(amount_arg.replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "⚠️ Please use a valid positive amount in the format: `/add 45.50 dinner`",
                parse_mode="Markdown",
            )
            return

        description = description_arg
        if not description:
            await message.answer(
                "⚠️ Please provide a description after the amount: `/add 45.50 dinner`",
                parse_mode="Markdown",
            )
            return

        await state.update_data(amount=amount, description=description)
        await state.set_state(AddExpenseStates.SELECT_PARTICIPANTS)

        async with get_session() as session:
            user_repo = UserRepository(session)
            group_repo = GroupRepository(session)
            user = await user_repo.get_by_telegram_id(message.from_user.id)
            group = await group_repo.get_user_group(user.id)
            members = await group_repo.get_members(group.id)
            member_ids = [m.id for m in members]

        await state.update_data(
            selected_ids=member_ids,
            payer_db_id=user.id,
            members_cache=[{"id": m.id, "name": m.name} for m in members],
        )

        await message.answer(
            f"👥 Select participants (default: all members).\nTap to toggle, then *Done*:",
            reply_markup=participants_keyboard(members, member_ids, user.id),
            parse_mode="Markdown",
        )
        return

    await state.set_state(AddExpenseStates.WAITING_AMOUNT)
    await message.answer("💰 Enter the expense amount (e.g. `45.50`):", parse_mode="Markdown")


@router.message(AddExpenseStates.WAITING_AMOUNT)
async def process_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Please enter a valid positive number:")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddExpenseStates.WAITING_DESCRIPTION)
    await message.answer("📝 What was this expense for?")


@router.message(AddExpenseStates.WAITING_DESCRIPTION)
async def process_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    if not description:
        await message.answer("⚠️ Description cannot be empty. Try again:")
        return

    await state.update_data(description=description)

    async with get_session() as session:
        user_repo = UserRepository(session)
        group_repo = GroupRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        group = await group_repo.get_user_group(user.id)
        members = await group_repo.get_members(group.id)
        member_ids = [m.id for m in members]

    await state.update_data(
        selected_ids=member_ids,  # default: all
        payer_db_id=user.id,
    )
    await state.set_state(AddExpenseStates.SELECT_PARTICIPANTS)

    data = await state.get_data()
    await message.answer(
        f"👥 Select participants (default: all members).\nTap to toggle, then *Done*:",
        reply_markup=participants_keyboard(members, member_ids, user.id),
        parse_mode="Markdown",
    )
    await state.update_data(members_cache=[
        {"id": m.id, "name": m.name} for m in members
    ])


@router.callback_query(AddExpenseStates.SELECT_PARTICIPANTS, F.data.startswith(CB_PARTICIPANT))
async def toggle_participant(callback: CallbackQuery, state: FSMContext) -> None:
    uid = int(callback.data.removeprefix(CB_PARTICIPANT))
    data = await state.get_data()
    selected_ids: List[int] = list(data.get("selected_ids", []))
    members_cache = data.get("members_cache", [])
    original_ids = selected_ids.copy()

    if uid in selected_ids:
        if len(selected_ids) > 1:  # keep at least one
            selected_ids.remove(uid)
        else:
            await callback.answer("At least one participant must remain.", show_alert=False)
            return
    else:
        selected_ids.append(uid)

    if selected_ids == original_ids:
        await callback.answer()
        return

    await state.update_data(selected_ids=selected_ids)

    # Rebuild User-like objects from cache
    from types import SimpleNamespace
    members = [SimpleNamespace(**m) for m in members_cache]
    payer_db_id = data.get("payer_db_id")

    await callback.message.edit_reply_markup(
        reply_markup=participants_keyboard(members, selected_ids, payer_db_id)
    )
    await callback.answer()


@router.callback_query(AddExpenseStates.SELECT_PARTICIPANTS, F.data == CB_PARTICIPANTS_DONE)
async def finalize_expense(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    amount = data["amount"]
    description = data["description"]
    selected_ids = data["selected_ids"]

    async with get_session() as session:
        service = ExpenseService(session)
        expense, group = await service.add_expense(
            telegram_id=callback.from_user.id,
            amount=amount,
            description=description,
            participant_ids=selected_ids,
        )
        share = round(amount / len(selected_ids), 2)

    await state.clear()
    await callback.message.edit_text(
        f"✅ *Expense recorded!*\n\n"
        f"📋 *{description}*\n"
        f"💰 Total: `{format_amount(amount)}`\n"
        f"👥 Split: `{format_amount(share)}` per person\n"
        f"🏠 Group: {group.name}",
        parse_mode="Markdown",
    )
    await callback.answer("Expense added!")


# ── /pay ───────────────────────────────────────────────────────────────────────

@router.message(Command(CMD_PAY))
async def cmd_pay(message: Message) -> None:
    text = (message.text or "").strip()
    parts = text.split()
    
    if len(parts) < 3:
        await message.answer(
            "⚠️ Please use the format: `/pay <amount> @<username>`\n"
            "Example: `/pay 50 @john`",
            parse_mode="Markdown",
        )
        return

    try:
        amount = float(parts[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Please provide a valid positive amount.")
        return

    recipient_username = parts[2]
    if not recipient_username.startswith('@'):
        await message.answer("⚠️ Please specify the recipient with @username format.")
        return

    async with get_session() as session:
        service = ExpenseService(session)
        try:
            settlement, payer, recipient = await service.pay_user(
                telegram_id=message.from_user.id,
                amount=amount,
                recipient_username=recipient_username,
            )
            # Get group name
            group_repo = GroupRepository(session)
            group = await group_repo.get_by_id(settlement.group_id)
        except LookupError as e:
            await message.answer(f"⚠️ {e}")
            return
        except ValueError as e:
            await message.answer(f"⚠️ {e}")
            return

    await message.answer(
        f"✅ *Payment recorded!*\n\n"
        f"💰 Amount: `{format_amount(amount)}`\n"
        f"👤 From: *{payer.name}*\n"
        f"👥 To: *{recipient.name}*\n"
        f"🏠 Group: {group.name}",
        parse_mode="Markdown",
    )


# ── /balance ───────────────────────────────────────────────────────────────────

@router.message(Command(CMD_BALANCE))
async def cmd_balance(message: Message) -> None:
    async with get_session() as session:
        service = ExpenseService(session)
        try:
            transactions, user = await service.get_group_balances(message.from_user.id)
        except LookupError as e:
            await message.answer(f"⚠️ {e}")
            return

    text = format_balance_message(transactions, user.id)
    await message.answer(text, parse_mode="Markdown")


# ── /history ───────────────────────────────────────────────────────────────────

@router.message(Command(CMD_HISTORY))
async def cmd_history(message: Message) -> None:
    async with get_session() as session:
        service = ExpenseService(session)
        try:
            expenses, group = await service.get_group_history(message.from_user.id)
        except LookupError as e:
            await message.answer(f"⚠️ {e}")
            return

    if not expenses:
        await message.answer("📭 No expenses recorded yet.")
        return

    lines = [f"📜 *Last expenses in {group.name}:*\n"]
    for exp in expenses:
        date = exp.created_at.strftime("%b %d")
        participants = ", ".join(p.user.name for p in exp.participants)
        lines.append(
            f"• `{format_amount(exp.amount)}` — *{exp.description}*\n"
            f"  Paid by: {exp.payer.name} | {date}\n"
            f"  Split with: {participants}"
        )

    await message.answer("\n\n".join(lines), parse_mode="Markdown")


# ── /settle ────────────────────────────────────────────────────────────────────

@router.message(Command(CMD_SETTLE))
async def cmd_settle(message: Message) -> None:
    async with get_session() as session:
        service = ExpenseService(session)
        try:
            transactions, user = await service.get_group_balances(message.from_user.id)
        except LookupError as e:
            await message.answer(f"⚠️ {e}")
            return

    my_debts = [t for t in transactions if t.debtor.id == user.id]
    if not my_debts:
        await message.answer("✅ You don't owe anyone anything right now!")
        return

    await message.answer(
        "💳 Select a debt to settle:",
        reply_markup=settle_keyboard(transactions, user.id),
    )


@router.callback_query(F.data.startswith(CB_SETTLE_DEBT))
async def process_settle_select(callback: CallbackQuery, state: FSMContext) -> None:
    creditor_id = int(callback.data.removeprefix(CB_SETTLE_DEBT))

    async with get_session() as session:
        service = ExpenseService(session)
        transactions, user = await service.get_group_balances(callback.from_user.id)

    matching = [t for t in transactions if t.debtor.id == user.id and t.creditor.id == creditor_id]
    if not matching:
        await callback.answer("Debt not found.", show_alert=True)
        return

    total = sum(t.amount for t in matching)
    creditor_name = matching[0].creditor.name

    await state.set_state(SettleStates.CONFIRM)
    await state.update_data(creditor_id=creditor_id, amount=total, creditor_name=creditor_name)

    await callback.message.edit_text(
        f"💳 Confirm payment of `{format_amount(total)}` to *{creditor_name}*?",
        parse_mode="Markdown",
        reply_markup=settle_confirm_keyboard(creditor_id, total, creditor_name),
    )
    await callback.answer()


@router.callback_query(SettleStates.CONFIRM, F.data.startswith(CB_SETTLE_CONFIRM))
async def process_settle_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    creditor_id = int(callback.data.removeprefix(CB_SETTLE_CONFIRM))

    async with get_session() as session:
        service = ExpenseService(session)
        try:
            amount = await service.settle_debt(callback.from_user.id, creditor_id)
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return

    await state.clear()
    data = await state.get_data()
    creditor_name = (await state.get_data()).get("creditor_name", "your roommate")

    await callback.message.edit_text(
        f"✅ *Debt settled!*\n\nYou paid `{format_amount(amount)}` to *{creditor_name}*.",
        parse_mode="Markdown",
    )
    await callback.answer("Settled!")


@router.callback_query(F.data == "settle:cancel")
async def process_settle_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Settlement cancelled.")
    await callback.answer()
