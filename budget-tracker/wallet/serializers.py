from rest_framework import serializers

from .models import Transaction, Account


class TransactionSerializer (serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['description', 'credit_account', 'debit_account', 'date', 'amount', ]

    def clean(self):
        pass


class AccountSerializer (serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['title', 'category']

