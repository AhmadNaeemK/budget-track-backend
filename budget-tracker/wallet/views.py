from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Transaction, Wallet, Account
from .serializers import TransactionSerializer, AccountSerializer

from django.contrib.auth import get_user_model


class TransactionList(APIView):

    def get(self, request, format=None):
        if request.GET.get('all'):
            transactions = Transaction.objects.filter(user_id=request.user.id).order_by('-transaction_date')[:5]
        else:
            transactions = Transaction.objects.filter(user_id=request.user.id).order_by('-transaction_date')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    def post(self, request):
        request.data.update({'user': request.user.id})
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        transactionId = request.data.pop('transactionId')
        request.data['amount'] = int(request.data['amount'])
        transaction = Transaction.objects.get(pk=transactionId)
        serializer = TransactionSerializer(transaction, request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            transaction = Transaction.objects.get(pk=request.data.get('transactionID'))
            transaction.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AccountList(APIView):

    def get(self, request, format=None):
        wallet = Wallet.objects.filter(user_id=request.user.id)[0]
        if request.GET.get('cash') == 'true':
            accounts = Account.objects.filter(wallet=wallet, category='Cash')
        elif request.GET.get('cash') == 'false':
            accounts = Account.objects.filter(wallet=wallet).exclude(category='Cash')
        elif request.GET.get('getAll'):
            accounts = Account.objects.filter(wallet=wallet)

        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
