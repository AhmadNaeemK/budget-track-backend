from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters, serializers
from rest_framework.exceptions import ValidationError

from django.db.models import Q, Sum
from django.http import HttpResponse

from .models import Transaction, CashAccount, SplitTransaction, TransactionCategories
from .utils import SplitTransactionUtils, TransactionUtils
from accounts.models import EmailAuthenticatedUser as User
from accounts.serializers import UserSerializer

from .serializers import TransactionSerializer, CashAccountSerializer, ScheduledTransactionSerializer
from .serializers import SplitTransactionSerializer, MaxSplitsDueSerializer

from .filters import TransactionFilterBackend, ScheduledTransactionFilterBackend, ExpenseFilterBackend
from .filters import IncomeFilterBackend

from datetime import datetime

from .tasks import send_all_notification
from .services import Notification

from .ReportMaker import ReportMaker


class ExpenseListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [TransactionFilterBackend, ExpenseFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title']
    ordering = ['-transaction_time']

    def perform_create(self, serializer):
        if serializer.validated_data.get('category') == TransactionCategories.Income.value:
            raise serializers.ValidationError('Income can not be an expense')
        account = CashAccount.objects.get(pk=serializer.initial_data.get('cash_account'))
        account.balance = TransactionUtils.get_new_account_balance(
            account.balance,
            serializer.validated_data.get('amount'),
            serializer.validated_data.get('category')
        )
        account.save()
        serializer.save()


class ExpenseView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [TransactionFilterBackend, ExpenseFilterBackend, filters.OrderingFilter]

    def perform_update(self, serializer):
        account = serializer.instance.cash_account
        account.balance = TransactionUtils.get_new_account_balance(
            account.balance + serializer.instance.amount,
            serializer.validated_data.get('amount'),
            serializer.instance.category
        )
        account.save()
        serializer.save()
        serializer.save()

    def perform_destroy(self, instance):
        instance.cash_account.balance = instance.cash_account.balance + instance.amount
        instance.cash_account.save()
        instance.delete()


class IncomeListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [TransactionFilterBackend, IncomeFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title']
    ordering = ['-transaction_time']

    def perform_create(self, serializer):
        if serializer.validated_data.get('category') != TransactionCategories.Income.value:
            raise ValidationError('Income can not be an expense')
        account = CashAccount.objects.get(pk=serializer.initial_data.get('cash_account'))
        account.balance = TransactionUtils.get_new_account_balance(
            account.balance,
            serializer.validated_data.get('amount'),
            serializer.validated_data.get('category')
        )
        account.save()
        serializer.save()


class IncomeView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [TransactionFilterBackend, IncomeFilterBackend, filters.OrderingFilter]

    def perform_update(self, serializer):
        account = serializer.instance.cash_account
        account.balance = TransactionUtils.get_new_account_balance(
            account.balance - serializer.instance.amount,
            serializer.validated_data.get('amount'),
            serializer.instance.category
        )
        account.save()
        serializer.save()

    def perform_destroy(self, instance):
        instance.cash_account.balance = instance.cash_account.balance - instance.amount
        instance.cash_account.save()
        instance.delete()


class CashAccountListView(generics.ListCreateAPIView):
    serializer_class = CashAccountSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title']
    ordering = ['-creation_time']

    def get_queryset(self):
        accounts = CashAccount.objects.filter(user=self.request.user.id).order_by('-creation_time')
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
        def get_total_expenses(category, account):
            total_category_expenses = Transaction.objects.filter(user=request.user.id,
                                                                 category=category,
                                                                 cash_account=account,
                                                                 transaction_time__month=request.GET.get('month'),
                                                                 scheduled=False
                                                                 ).aggregate(Sum('amount')
                                                                             )['amount__sum']
            return total_category_expenses or 0

        accounts = CashAccount.objects.filter(user=request.user.id)
        data = {}
        for account in accounts:
            data[account.title] = [(category[1], get_total_expenses(category[0], account))
                                   for category in TransactionCategories.choices if
                                   get_total_expenses(category[0], account) > 0
                                   and category[1] != 'Income']
        return Response(data)


class MonthlyTransactionDataView(APIView):

    def get_month_data(self, user_id, month):
        transactions = Transaction.objects.filter(user=user_id, transaction_time__month=month,
                                                  transaction_time__year=datetime.now().year, scheduled=False
                                                  )
        total_expenses = transactions.exclude(category=TransactionCategories.Income.value
                                              ).aggregate(Sum('amount'))['amount__sum']
        total_income = transactions.filter(category=TransactionCategories.Income.value).aggregate(Sum('amount'))[
            'amount__sum']
        return total_income, total_expenses

    def get(self, request):
        data = {
            'income': [],
            'expense': []
        }
        for month in range(1, 13):
            month_data = self.get_month_data(request.user.id, month)
            data['income'].append(month_data[0])
            data['expense'].append(month_data[1])

        return Response(data)


class ScheduledTransactionListView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all().order_by('transaction_time')
    serializer_class = ScheduledTransactionSerializer
    filter_backends = [ScheduledTransactionFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title']


class ScheduledTransactionView(generics.RetrieveDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = ScheduledTransactionSerializer
    filter_backends = [ScheduledTransactionFilterBackend, filters.OrderingFilter]


class SplitTransactionListView(generics.ListCreateAPIView):
    serializer_class = SplitTransactionSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'creator__username', 'paying_friend__username']

    def get_queryset(self):
        return SplitTransaction.objects.filter(Q(creator=self.request.user.id) | Q(paying_friend=self.request.user.id) |
                                               Q(all_friends_involved__id=self.request.user.id)
                                               ).distinct().order_by('creator__username')

    def perform_create(self, serializer):
        split = serializer.save()
        payment_transaction_title = "{split_title} paid by {split_creator}".format(split_title=split.title,
                                                                                   split_creator=split.creator.username)
        payer_cash_account = CashAccount.objects.get(user=split.paying_friend, title='Cash')
        payment_transaction_serializer = TransactionSerializer(data={'title': payment_transaction_title,
                                                                     'user': split.paying_friend.id,
                                                                     'cash_account': payer_cash_account.id,
                                                                     'category': split.category,
                                                                     'amount': split.total_amount,
                                                                     'split_expense': split.id
                                                                     })
        if payment_transaction_serializer.is_valid():
            ExpenseListView().perform_create(payment_transaction_serializer)
            send_all_notification.delay(notification_type=Notification.SPLIT_INCLUDE_NOTIFICATION,
                                        data={
                                            'split': SplitTransactionSerializer(split).data
                                        })

        else:
            SplitTransaction.objects.get(pk=split.id).delete()
            raise serializers.ValidationError(payment_transaction_serializer.errors)


class SplitTransactionView(generics.RetrieveDestroyAPIView):
    queryset = SplitTransaction.objects.all()
    serializer_class = SplitTransactionSerializer


class PaySplit(APIView):

    def post(self, request):
        split = SplitTransaction.objects.get(pk=request.data.get('split_id'))
        payable, split_payment, paid_amount = SplitTransactionUtils.get_user_payable_amount(request.user.id, split)
        if int(request.data.get('amount')) > (split_payment - paid_amount):
            raise ValidationError('Entering More Than Required Amount')

        payment_transaction_title = f"{split.title} paid by {split.creator.username}"
        payer_cash_account = CashAccount.objects.get(user=request.user.id, title='Cash')
        payment_transaction_serializer = TransactionSerializer(data={'title': payment_transaction_title,
                                                                     'user': request.user.id,
                                                                     'cash_account': payer_cash_account.id,
                                                                     'category': split.category,
                                                                     'amount': request.data.get(
                                                                         'amount'),
                                                                     'split_expense': split.id
                                                                     })
        user = User.objects.get(pk=request.user.id)
        receiving_transaction_title = f"Payment for {split.title} paid by {user.username}"
        receiver_cash_account = CashAccount.objects.get(user=split.paying_friend.id, title='Cash')
        receiving_transaction_serializer = TransactionSerializer(data={'title': receiving_transaction_title,
                                                                       'user': split.paying_friend.id,
                                                                       'cash_account': receiver_cash_account.id,
                                                                       'category': TransactionCategories.choices[0][0],
                                                                       'amount': request.data.get('amount'),
                                                                       'split_expense': split.id
                                                                       })

        if payment_transaction_serializer.is_valid() and receiving_transaction_serializer.is_valid():
            ExpenseListView().perform_create(payment_transaction_serializer)
            IncomeListView().perform_create(receiving_transaction_serializer)
            send_all_notification.delay(notification_type=Notification.SPLIT_PAYMENT_NOTIFICATION,
                                        data={
                                            'split': SplitTransactionSerializer(split).data,
                                            'user': UserSerializer(user).data,
                                            'payment': int(request.data.get('amount')),
                                            'split_payment': split_payment,
                                            'paid_amount': paid_amount
                                        })
            return Response('Payment Successful')

        else:
            return Response(payment_transaction_serializer.errors)


class TransactionsWithSplit(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user.id, split_expense__isnull=False)


class SplitPaymentData(APIView):

    def get(self, request, pk):
        split = SplitTransaction.objects.get(pk=pk)
        payable, required, paid = SplitTransactionUtils.get_user_payable_amount(request.user.id, split)
        return Response({'required': payable, 'paid': paid})


class MaximumSplitsDue(generics.ListAPIView):
    serializer_class = MaxSplitsDueSerializer

    def get_queryset(self):
        splits = SplitTransaction.objects.filter(
            Q(creator=self.request.user.id) | Q(paying_friend=self.request.user.id) |
            Q(all_friends_involved__id=self.request.user.id)
        ).distinct().order_by('creator__username')

        payable_splits = [{'split': split,
                           'payable_amount': SplitTransactionUtils.get_user_payable_amount(
                               user_id=self.request.user.id,
                               split=split)[0]}
                          for split in splits]
        payable_splits.sort(reverse=True, key=lambda split: split['payable_amount'])

        return payable_splits[:5]


class DownloadTransactionReportView(APIView):

    def get(self, request):
        request_data = {**request.GET, 'user_id': request.user.id}
        report = ReportMaker(request_data).make_report()
        report_name = f'{request.user.username}_Transactions_Report.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{report_name}"'},
        )
        response.write(report)
        return response
