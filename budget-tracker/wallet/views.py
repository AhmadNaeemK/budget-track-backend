from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, filters

from .models import Transaction, CashAccount
from .serializers import TransactionSerializer, CashAccountSerializer

import datetime


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


# class CashAccountList(APIView):
#
#     def get(self, request, format=None):
#         if request.GET.get('getAll') == 'true':
#             accounts = CashAccount.objects.filter(user=request.user.id, category='Cash')
#         else:
#             accounts = CashAccount.objects.filter(user=request.user.id, category='Cash')
#
#         serializer = CashAccountSerializer(accounts, many=True)
#         return Response(serializer.data)
#
#     def post(self, request):
#         request.data.update({'user': request.user.id})
#         serializer = CashAccountSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def delete(self, request):
#         try:
#             account = CashAccount.objects.get(pk=request.data.get('accountId'))
#             account.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#
#     def put(self, request):
#         account_id = request.data.pop('accountId')
#         account = CashAccount.objects.get(pk=account_id)
#         serializer = CashAccountSerializer(account, request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionCategoryChoicesList(APIView):

    def get(self, request):
        choices = Transaction.Categories.choices

        return Response(choices)
