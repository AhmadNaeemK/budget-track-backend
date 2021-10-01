from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters, pagination, status, serializers

from django.db.models import Q

from .models import Transaction, CashAccount, SplitTransaction, TransactionCategories
from accounts.models import EmailAuthenticatedUser as User

from .serializers import TransactionSerializer, CashAccountSerializer, ScheduledTransactionSerializer
from .serializers import SplitTransactionSerializer

from .filters import TransactionFilterBackend, ScheduledTransactionFilterBackend, ExpenseFilterBackend
from .filters import IncomeFilterBackend

from datetime import datetime


class StandardPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ExpenseListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [TransactionFilterBackend, ExpenseFilterBackend, filters.OrderingFilter]
    ordering = ['-transaction_time']

    def perform_create(self, serializer):
        if serializer.validated_data.get('category') == TransactionCategories.Income.value:
            raise serializers.ValidationError('Income can not be an expense')
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


class IncomeListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [TransactionFilterBackend, IncomeFilterBackend, filters.OrderingFilter]
    ordering = ['-transaction_time']

    def perform_create(self, serializer):
        if serializer.validated_data.get('category') != TransactionCategories.Income.value:
            raise serializers.ValidationError('Income can not be an expense')
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
        choices = TransactionCategories.choices

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
                                   for choice in TransactionCategories.choices if
                                   get_total_expenses(choice[0], account) > 0
                                   and choice[1] != 'Income']
        return Response(data)


class MonthlyTransactionDataView(APIView):
    def get(self, request):
        def get_total_of_transactions(transactions):
            return sum([transaction.amount for transaction in transactions])

        def get_month_data(month):
            expenses = Transaction.objects.filter(user=request.user.id, transaction_time__month=month,
                                                  transaction_time__year=datetime.now().year
                                                  )
            expenses = expenses.exclude(category=TransactionCategories.Income.value)
            incomes = Transaction.objects.filter(user=request.user.id, category=TransactionCategories.Income.value,
                                                 transaction_time__month=month,
                                                 transaction_time__year=datetime.now().year)
            return get_total_of_transactions(incomes), get_total_of_transactions(expenses)

        data = {
            'income': [],
            'expense': []
        }

        for month in range(1, 13):
            month_data = get_month_data(month)
            data['income'].append(month_data[0])
            data['expense'].append(month_data[1])

        return Response(data)


class ScheduledTransactionListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = ScheduledTransactionSerializer
    filter_backends = [ScheduledTransactionFilterBackend, filters.OrderingFilter]


class ScheduledTransactionView(generics.RetrieveDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = ScheduledTransactionSerializer
    filter_backends = [ScheduledTransactionFilterBackend, filters.OrderingFilter]


class SplitTransactionListView(generics.ListCreateAPIView):
    serializer_class = SplitTransactionSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return SplitTransaction.objects.filter(Q(creator=self.request.user.id) | Q(paying_friend=self.request.user.id) |
                                               Q(all_friends_involved__id=self.request.user.id)
                                               ).distinct().order_by('creator__username')


class SplitTransactionView(generics.RetrieveDestroyAPIView):
    queryset = SplitTransaction.objects.all()
    serializer_class = SplitTransactionSerializer


class PaySplit(APIView):

    def post(self, request):
        split = SplitTransaction.objects.get(pk=request.data.get('split_id'))

        payment_transaction_title = "{split_title} paid by {split_creator}".format(split_title=split.title,
                                                                                   split_creator=split.creator)
        payment_transaction_serializer = TransactionSerializer(data={'title': payment_transaction_title,
                                                                     'user': request.user.id,
                                                                     'cash_account': CashAccount.objects.get(
                                                                         user=request.user.id,
                                                                         title='Cash').id,
                                                                     'category': split.category,
                                                                     'amount': request.data.get('amount'),
                                                                     'split_expense': split.id
                                                                     })
        user = User.objects.get(pk=request.user.id)
        receiving_transaction_title = "Payment for {split_title} paid by {user}".format(split_title=split.title,
                                                                                        user=user.username)
        receiving_transaction_serializer = TransactionSerializer(data={'title': receiving_transaction_title,
                                                                       'user': split.paying_friend.id,
                                                                       'cash_account': CashAccount.objects.get(
                                                                           user=split.paying_friend.id,
                                                                           title='Cash').id,
                                                                       'category': TransactionCategories.choices[0][0],
                                                                       'amount': request.data.get('amount'),
                                                                       'split_expense': split.id
                                                                       })

        if payment_transaction_serializer.is_valid() and receiving_transaction_serializer.is_valid():
            payment_transaction_serializer.save()
            receiving_transaction_serializer.save()

            return Response("Payment Successful")

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class TransactionsWithSplit(generics.ListAPIView):
    serializer_class = TransactionSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user.id, split_expense__isnull=False)
