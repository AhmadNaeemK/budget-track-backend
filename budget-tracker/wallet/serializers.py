from rest_framework import serializers

from .models import Transaction, Account


class TransactionSerializer (serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'title','description', 'user', 'credit_account', 'debit_account', 'transaction_date', 'amount', ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['credit_account'] = Account.objects.get(pk=data['credit_account']).title
        data['debit_account'] = Account.objects.get(pk=data['debit_account']).title
        return data


class AccountSerializer (serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'title', 'category', 'wallet']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['debit'] = Account.objects.get(pk=data['id']).get_debit()
        data['credit'] = Account.objects.get(pk=data['id']).get_credit()
        return data