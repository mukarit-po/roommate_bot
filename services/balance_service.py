"""
services/balance_service.py — Core business logic for balance calculation
and debt optimization (minimize number of transactions).
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

from models import User


def format_amount(amount: float) -> str:
    """Format amount without currency symbol and trailing .00 for whole numbers."""
    if amount == int(amount):
        return str(int(amount))
    return f"{amount:.2f}"


@dataclass
class DebtEntry:
    debtor: User
    creditor: User
    amount: float


def compute_balances(
    participants: list,  # List[ExpenseParticipant]
    expenses: list,      # List[Expense]
    users_by_id: Dict[int, User],
) -> Dict[int, float]:
    """
    For each user, compute their net balance within the group.
    Positive = they are owed money. Negative = they owe money.
    """
    balances: Dict[int, float] = defaultdict(float)

    for expense in expenses:
        # Payer gains the full amount (they're owed)
        balances[expense.payer_id] += expense.amount

    for participant in participants:
        # Each participant owes their share
        balances[participant.user_id] -= participant.share_amount

    return dict(balances)


def optimize_debts(balances: Dict[int, float], users_by_id: Dict[int, User]) -> List[DebtEntry]:
    """
    Greedy debt simplification algorithm.
    Minimizes the number of transactions needed to settle all debts.
    """
    # Split into creditors (positive balance) and debtors (negative balance)
    creditors: List[Tuple[int, float]] = sorted(
        [(uid, bal) for uid, bal in balances.items() if bal > 0.005],
        key=lambda x: x[1],
    )
    debtors: List[Tuple[int, float]] = sorted(
        [(uid, -bal) for uid, bal in balances.items() if bal < -0.005],
        key=lambda x: x[1],
    )

    transactions: List[DebtEntry] = []
    c_idx, d_idx = 0, 0

    while c_idx < len(creditors) and d_idx < len(debtors):
        creditor_id, credit = creditors[c_idx]
        debtor_id, debt = debtors[d_idx]

        settle_amount = min(credit, debt)

        if settle_amount > 0.005:
            transactions.append(
                DebtEntry(
                    debtor=users_by_id[debtor_id],
                    creditor=users_by_id[creditor_id],
                    amount=round(settle_amount, 2),
                )
            )

        # Update remaining balances
        remaining_credit = credit - settle_amount
        remaining_debt = debt - settle_amount

        if remaining_credit < 0.005:
            c_idx += 1
        else:
            creditors[c_idx] = (creditor_id, remaining_credit)

        if remaining_debt < 0.005:
            d_idx += 1
        else:
            debtors[d_idx] = (debtor_id, remaining_debt)

    return transactions


def format_balance_message(
    transactions: List[DebtEntry],
    current_user_id: int,
) -> str:
    """Format debt summary for display in Telegram."""
    if not transactions:
        return "✅ All debts are settled! Everyone is even."

    lines = ["💸 *Current Debts:*\n"]
    for t in transactions:
        debtor_name = t.debtor.name
        creditor_name = t.creditor.name
        arrow = "➡️"
        if t.debtor.id == current_user_id:
            line = f"👤 *You* owe *{creditor_name}* — `{format_amount(t.amount)}`"
        elif t.creditor.id == current_user_id:
            line = f"✅ *{debtor_name}* owes *you* — `{format_amount(t.amount)}`"
        else:
            line = f"• {debtor_name} {arrow} {creditor_name}: `{format_amount(t.amount)}`"
        lines.append(line)

    return "\n".join(lines)
