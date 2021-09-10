from rest_framework import serializers

from .models import Transaction, Account, Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

class TransactionSerializer (serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'title', 'description', 'user', 'credit_account', 'debit_account', 'transaction_date', 'amount']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['credit_account'] = Account.objects.get(pk=data['credit_account']).title
        data['debit_account'] = Account.objects.get(pk=data['debit_account']).title
        return data

    def validate(self, data):

        def get_from_request_or_instance(attr_name):
            if attr_name in data:
                return data[attr_name]
            if self.instance and hasattr(self.instance, attr_name):
                return getattr(self.instance, attr_name)
            return None

        credit_account = get_from_request_or_instance('credit_account')
        debit_account = get_from_request_or_instance('debit_account')
        amount = get_from_request_or_instance('amount')

        if credit_account.category not in [Account.Categories.Cash.value, Account.Categories.Salary.value]:
            raise serializers.ValidationError("Credit Account can only be a Cash or Salary type account")

        if credit_account == debit_account:
            raise serializers.ValidationError("Credit Account can not be same as debit account")

        if amount > credit_account.get_balance() and credit_account.category != Account.Categories.Salary.value:
            raise serializers.ValidationError("Credit Account does not have enough Balance")

        if debit_account.category == Account.Categories.Salary.value:
            raise serializers.ValidationError("Debit Account can not be a Salary type account")

        if self.partial:
            if self.instance and self.instance.credit_account.get_balance() + self.instance.amount < amount:
                raise serializers.ValidationError("Credit Account does not have enough Balance")

        return data


class AccountSerializer (serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'title', 'category', 'wallet', 'budget_limit']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['debit'] = Account.objects.get(pk=data['id']).get_debit()
        data['credit'] = Account.objects.get(pk=data['id']).get_credit()
        data['category'] = Account.Categories.choices[data['category']-1]
        data['balance'] = data['debit'] - data['credit']
        return data
