import datetime
from rest_framework import filters
from wallet.models import TransactionCategories


class TransactionFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        month = request.GET.get('month') or datetime.date.today().month
        transactions = queryset.filter(user=request.user.id,
                                       transaction_time__month=month,
                                       scheduled=False)
        return transactions


class ScheduledTransactionFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        transactions = queryset.filter(user=request.user.id, scheduled=True)
        return transactions


class ExpenseFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        income = TransactionCategories.Income.value
        expenses = queryset.exclude(category=income)
        return expenses


class IncomeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        income = TransactionCategories.Income.value
        expenses = queryset.filter(category=income)
        return expenses
