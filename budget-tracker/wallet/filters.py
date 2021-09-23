import datetime
from rest_framework import filters
from .models import Transaction


class TransactionFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        month = request.GET.get('month') or datetime.date.today().month
        transactions = queryset.filter(user=request.user.id, transaction_time__month=month, scheduled=False)
        return transactions


class ScheduledTransactionFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        month = request.GET.get('month') or datetime.date.today().month
        transactions = queryset.filter(user=request.user.id, transaction_time__month=month, scheduled=True)
        return transactions


class ExpenseFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        income = Transaction.Categories.Income.value
        expenses = queryset.exclude(category=income)
        return expenses
