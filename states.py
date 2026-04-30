"""
states.py — FSM state groups for all bot flows.
"""

from aiogram.fsm.state import State, StatesGroup


class CreateGroupStates(StatesGroup):
    WAITING_NAME = State()


class JoinGroupStates(StatesGroup):
    SELECTING_GROUP = State()


class AddExpenseStates(StatesGroup):
    WAITING_AMOUNT = State()
    WAITING_DESCRIPTION = State()
    SELECT_PARTICIPANTS = State()


class SettleStates(StatesGroup):
    CONFIRM = State()


class AdminMenuStates(StatesGroup):
    MAIN = State()
    VIEW_USERS = State()
    VIEW_GROUPS = State()
    VIEW_EXPENSES = State()
