from django.db.models import Sum

from .models import Transaction, TransactionCategories


class SplitTransactionUtils:

    def get_user_payable_amount(self, user_id, split):
        required_payment = split.total_amount // len(split.all_friends_involved.all())
        paid_amount = Transaction.objects.filter(user=user_id, split_expense=split).exclude(
            category=TransactionCategories.Income.value).aggregate(
            Sum('amount'))['amount__sum'] or 0
        payable = required_payment - paid_amount
        payable = payable if payable > 0 else 0
        return payable, required_payment, paid_amount


class TransactionUtils:

    def get_new_account_balance(self, prev_balance, amount, category):
        amount = amount if category == TransactionCategories.Income.value else -amount
        return prev_balance + amount
