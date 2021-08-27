from rest_framework import serializers

from .models import Transaction, Account


class TransactionSerializer (serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'description', 'credit_account', 'debit_account', 'transaction_date', 'amount', ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['credit_account'] = Account.objects.get(pk=data['credit_account']).title
        data['debit_account'] = Account.objects.get(pk=data['debit_account']).title
        return data


class AccountSerializer (serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['title', 'category']

