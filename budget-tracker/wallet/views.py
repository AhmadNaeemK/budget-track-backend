from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters, pagination, status

from .models import Transaction, CashAccount, SplitTransaction
from accounts.models import MyUser as User

from .serializers import TransactionSerializer, CashAccountSerializer, ScheduledTransactionSerializer
from .serializers import SplitTransactionSerializer
from .filters import TransactionFilterBackend, ScheduledTransactionFilterBackend, ExpenseFilterBackend


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
                                   for choice in Transaction.Categories.choices if
                                   get_total_expenses(choice[0], account) > 0
                                   and choice[1] != 'Income']
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
        if self.request.GET.get('my_split') == 'true':
            splits = SplitTransaction.objects.filter(creator=self.request.user.id)
        else:
            splits = SplitTransaction.objects.filter(users_in_split__id__contains=self.request.user.id)
        return splits.order_by('id')


class SplitTransactionView(generics.RetrieveDestroyAPIView):
    queryset = SplitTransaction.objects.all().order_by('creator__username')
    serializer_class = SplitTransactionSerializer


class PaySplit(APIView):

    def post(self, request):
        split = SplitTransaction.objects.get(pk=request.data.get('split_id'))
        payment_transaction_title = "{split_title} payed by {split_creator}".format(split_title=split.title,
                                                                                    split_creator=split.creator)
        payment_transaction_serializer = TransactionSerializer(data={'title': payment_transaction_title,
                                                                     'user': request.user.id,
                                                                     'cash_account': CashAccount.objects.get(
                                                                         user=request.user.id,
                                                                         title='Cash').id,
                                                                     'category': split.category,
                                                                     'amount': request.data.get('amount'),
                                                                     })
        user = User.objects.get(pk=request.user.id)
        receiving_transaction_title = "Payment for {split_title} payed by {user}".format(split_title=split.title,
                                                                                         user=user.username)
        receiving_transaction_serializer = TransactionSerializer(data={'title': receiving_transaction_title,
                                                                       'user': split.creator.id,
                                                                       'cash_account': CashAccount.objects.get(
                                                                           user=split.creator.id,
                                                                           title='Cash').id,
                                                                       'category': Transaction.Categories.choices[0][0],
                                                                       'amount': request.data.get('amount'),
                                                                       })

        if payment_transaction_serializer.is_valid() and receiving_transaction_serializer.is_valid():
            payment_transaction_serializer.save()
            receiving_transaction_serializer.save()

            split.payed_users.add(User.objects.get(pk=request.user.id))
            split.users_in_split.remove(User.objects.get(pk=request.user.id))

            return Response("Payment Successful")

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
