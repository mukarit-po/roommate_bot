"""
constants.py — All bot commands and callback data constants.
Avoids magic strings scattered across the codebase.
"""

# ── User Commands ──────────────────────────────────────────────────────────────
CMD_START = "start"
CMD_HELP = "help"
CMD_CREATE_GROUP = "create_group"
CMD_JOIN = "join"
CMD_ADD = "add"
CMD_BALANCE = "balance"
CMD_HISTORY = "history"
CMD_SETTLE = "settle"
CMD_PAY = "pay"
CMD_ADMIN = "admin"

# ── Admin Callback Prefixes ────────────────────────────────────────────────────
CB_ADMIN_STATS = "admin:stats"
CB_ADMIN_USERS = "admin:users"
CB_ADMIN_GROUPS = "admin:groups"
CB_ADMIN_EXPENSES = "admin:expenses"
CB_ADMIN_BACK = "admin:back"

CB_USER_VIEW = "admin:user:"          # + user_id
CB_GROUP_VIEW = "admin:group:"        # + group_id
CB_EXPENSE_VIEW = "admin:expense:"    # + expense_id
CB_EXPENSE_DELETE = "admin:expense:del:"  # + expense_id
CB_EXPENSE_DELETE_CONFIRM = "admin:expense:delconfirm:"  # + expense_id

# Pagination  — format: "admin:page:<section>:<page_num>"
CB_PAGE = "admin:page:"

# ── User Flow Callbacks ────────────────────────────────────────────────────────
CB_JOIN_GROUP = "join:"               # + group_id
CB_PARTICIPANT = "participant:"       # + user_id  (toggle)
CB_PARTICIPANTS_DONE = "participants:done"
CB_SETTLE_DEBT = "settle:"           # + debtor_id:creditor_id
CB_SETTLE_CONFIRM = "settle:confirm:" # + debtor_id:creditor_id

# ── Messages ───────────────────────────────────────────────────────────────────
MSG_UNAUTHORIZED = "🚫 You are not authorized to use this command."
MSG_NOT_IN_GROUP = "⚠️ You are not in any group. Use /join or /create_group first."
MSG_NO_EXPENSES = "📭 No expenses found."
MSG_NO_USERS = "👤 No users found."
MSG_NO_GROUPS = "🏠 No groups found."
