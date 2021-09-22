from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, filters, pagination

from .models import Transaction, CashAccount, ScheduledTransaction
from .serializers import TransactionSerializer, CashAccountSerializer, ScheduledTransactionSerializer

import datetime


class StandardPagination(pagination.PageNumberPagination):
    page_size = 6
    page_query_param = 'page_size'
    max_page_size = 100


class TransactionFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        month = request.GET.get('month') or datetime.date.today().month
        transactions = queryset.filter(user=request.user.id, transaction_time__month=month)
        return transactions


class ExpenseFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        income = Transaction.Categories.Income.value
        expenses = queryset.exclude(category=income)
        return expenses


class ExpenseListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [TransactionFilterBackend, ExpenseFilterBackend, filters.OrderingFilter]
    ordering = ['-transaction_time']

    def perform_create(self, serializer):
        this_cash_account = serializer.validated_data.get('cash_account')
        new_balance = this_cash_account.balance - serializer.validated_data.get('amount')
        this_cash_account.balance = new_balance
        this_cash_account.save()
        serializer.save()


class ExpenseView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [TransactionFilterBackend, ExpenseFilterBackend, filters.OrderingFilter]

    def perform_update(self, serializer):
        this_cash_account = serializer.instance.cash_account
        new_balance = this_cash_account.balance + serializer.instance.amount - serializer.validated_data.get('amount')
        this_cash_account.balance = new_balance
        this_cash_account.save()
        serializer.save()

    def perform_destroy(self, instance):
        instance.cash_account.balance = instance.cash_account.balance + instance.amount
        instance.cash_account.save()
        instance.delete()


class IncomeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        income = Transaction.Categories.Income.value
        expenses = queryset.filter(category=income)
        return expenses


class IncomeListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [TransactionFilterBackend, IncomeFilterBackend, filters.OrderingFilter]
    ordering = ['-transaction_time']

    def perform_create(self, serializer):
        this_cash_account = serializer.validated_data.get('cash_account')
        new_balance = this_cash_account.balance + serializer.validated_data.get('amount')
        this_cash_account.balance = new_balance
        this_cash_account.save()
        serializer.save()


class IncomeView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [TransactionFilterBackend, IncomeFilterBackend, filters.OrderingFilter]

    def perform_update(self, serializer):
        this_cash_account = serializer.instance.cash_account
        new_balance = this_cash_account.balance - serializer.instance.amount + serializer.validated_data.get('amount')
        this_cash_account.balance = new_balance
        this_cash_account.save()
        serializer.save()

    def perform_destroy(self, instance):
        instance.cash_account.balance = instance.cash_account.balance - instance.amount
        instance.cash_account.save()
        instance.delete()


class CashAccountListView(generics.ListCreateAPIView):
    serializer_class = CashAccountSerializer

    def get_queryset(self):
        accounts = CashAccount.objects.filter(user=self.request.user.id)
        return accounts


class CashAccountView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CashAccountSerializer

    def get_queryset(self):
        accounts = CashAccount.objects.filter(user=self.request.user.id)
        return accounts


class TransactionCategoryChoicesList(APIView):

    def get(self, request):
        choices = Transaction.Categories.choices

        return Response(choices)


class ExpenseCategoryDataView(APIView):

    def get(self, request):
        def get_total_expenses(choice, account):
            category_expenses = Transaction.objects.filter(user=request.user.id, category=choice, cash_account=account,
                                                           transaction_time__month=request.GET.get('month'))
            total = sum([expense.amount for expense in category_expenses])
            return total

        accounts = CashAccount.objects.filter(user=request.user.id)
        data = {}
        for account in accounts:
            data[account.title] = [(choice[1], get_total_expenses(choice[0], account))
                                   for choice in Transaction.Categories.choices if get_total_expenses(choice[0], account) > 0
                                   and choice[1] != 'Income']
        return Response(data)


class ScheduledTransactionListView(generics.ListCreateAPIView):

    def get_queryset(self):
        return ScheduledTransaction.objects.filter(user=self.request.user.id)

    serializer_class = ScheduledTransactionSerializer


class ScheduledTransactionView(generics.RetrieveDestroyAPIView):

    def get_queryset(self):
        return ScheduledTransaction.objects.filter(user=self.request.user.id)

    serializer_class = ScheduledTransactionSerializer
