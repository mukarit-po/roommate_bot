# 🏠 Roommate Expense Bot

A production-ready Telegram bot for roommates to track shared expenses, calculate debts, and settle balances — with a fully-featured **in-bot Admin Panel**.

## ✨ Features

### 👤 User Features
| Command | Description |
|---|---|
| `/start` | Register and see welcome message |
| `/create_group` | Create a new roommate group |
| `/join` | Browse and join existing groups |
| `/add` | Record a shared expense (FSM flow) |
| `/balance` | See optimized debt summary |
| `/history` | View last 10 expenses |
| `/settle` | Mark debts as paid |

### 🔐 Admin Panel (`/admin`)
Secured by `ADMIN_CHAT_ID`. Fully navigable via inline keyboards.

```
[ 📊 Stats ] [ 👥 Users ]
[ 🏠 Groups ] [ 💸 Expenses ]
```

- **Stats**: Total users, groups, expenses, money tracked
- **Users**: Paginated list → click for full profile
- **Groups**: Paginated list → click for members & expense count
- **Expenses**: Paginated list → click for details → soft delete with confirmation

## 🛠 Tech Stack

- **Python 3.11+**
- **aiogram v3** — async Telegram bot framework
- **SQLAlchemy 2.0** (async) — ORM
- **aiosqlite** — SQLite async driver (swap for asyncpg for PostgreSQL)
- **pydantic-settings** — config management
- **FSM** — Finite State Machine for multi-step flows

## 📦 Setup

### 1. Clone & install

```bash
git clone <repo>
cd roommate_bot
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env:
# BOT_TOKEN=your_bot_token
# ADMIN_CHAT_ID=your_telegram_id
```

Get your bot token from [@BotFather](https://t.me/BotFather).  
Get your Telegram ID from [@userinfobot](https://t.me/userinfobot).

### 3. Run

```bash
python bot.py
```

The database (`roommate_bot.db`) is created automatically on first run.

### PostgreSQL (Production)

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/roommate_bot
```

```bash
pip install asyncpg
```

## 🗂 Project Structure

```
roommate_bot/
├── bot.py                  # Entry point — polling + router registration
├── config.py               # Settings via pydantic-settings
├── constants.py            # Commands, callback prefixes, messages
├── database.py             # Async engine + session factory
├── states.py               # FSM state groups
├── requirements.txt
├── .env.example
│
├── models/
│   ├── __init__.py
│   └── base.py             # User, Group, GroupMember, Expense,
│                           # ExpenseParticipant, Settlement
│
├── repositories/
│   ├── __init__.py
│   ├── user_repo.py        # CRUD + pagination for users
│   ├── group_repo.py       # CRUD + membership for groups
│   └── expense_repo.py     # CRUD + soft delete for expenses/settlements
│
├── services/
│   ├── __init__.py
│   ├── balance_service.py  # Debt computation + greedy optimization
│   └── expense_service.py  # High-level expense orchestration
│
├── keyboards/
│   ├── __init__.py
│   ├── user_keyboards.py   # Group join, participant toggle, settle UI
│   └── admin_keyboards.py  # Admin panel menus + pagination
│
└── handlers/
    ├── __init__.py
    ├── user_handlers.py    # All user commands + callback handlers
    └── admin_handlers.py   # Admin panel with full CRUD navigation
```

## 🧮 Debt Optimization Algorithm

Uses a **greedy creditor-debtor matching** algorithm that minimizes the number of transactions:

1. Compute each user's net balance (positive = owed, negative = owes)
2. Sort creditors and debtors by amount
3. Greedily match largest creditor with largest debtor
4. Generate one transaction per match

**Example**: 3 people, 6 possible raw transactions → reduced to 2 optimized payments.

## 🔄 Sample Bot Interaction

```
User: /add
Bot:  💰 Enter the expense amount:
User: 90
Bot:  📝 What was this expense for?
User: Groceries
Bot:  👥 Select participants (tap to toggle):
      ✅ Alice (payer)  ✅ Bob  ✅ Charlie
      [✔️ Done]
User: [taps Done]
Bot:  ✅ Expense recorded!
      📋 Groceries
      💰 Total: $90.00
      👥 Split: $30.00 per person

User: /balance
Bot:  💸 Current Debts:
      👤 You owe Alice — $30.00
      • Bob → Alice: $30.00
```

## 🔒 Security

- Admin auth is purely by `ADMIN_CHAT_ID` comparison
- All unauthorized `/admin` attempts return "You are not authorized"
- All callback handlers re-check admin status (no bypass via direct callback spam)
- Expenses use soft-delete (data preserved for audit)

## 🚀 Production Notes

- Replace `MemoryStorage` with `RedisStorage` for multi-instance deployments
- Add Alembic migrations for schema changes
- Use webhook mode (`dp.start_webhook`) behind a reverse proxy for production
- Add structured logging (JSON) for log aggregation
