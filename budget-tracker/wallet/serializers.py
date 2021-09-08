from rest_framework import serializers

from .models import Transaction, Account


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

        def my_get(attr_name):
            if attr_name in data:
                return data[attr_name]
            if self.instance and hasattr(self.instance, attr_name):
                return getattr(self.instance, attr_name)
            return None

        credit_account = my_get('credit_account')
        debit_account = my_get('debit_account')
        amount = my_get('amount')

        if credit_account.category not in ['Cash', 'Salary']:
            raise serializers.ValidationError("Credit Account can only be a Cash or Salary type account")

        if credit_account == debit_account:
            raise serializers.ValidationError("Credit Account can not be same as debit account")

        if amount > credit_account.get_balance() and credit_account.category != 'Salary':
            raise serializers.ValidationError("Credit Account does not have enough Balance")

        if debit_account.category == 'Salary':
            raise serializers.ValidationError("Debit Account can not be a Salary type account")

        if self.partial:
            if self.instance and self.instance.credit_account.get_balance() + self.instance.amount < amount:
                raise serializers.ValidationError("Credit Account does not have enough Balance")

        return data


class AccountSerializer (serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'title', 'category', 'wallet']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['debit'] = Account.objects.get(pk=data['id']).get_debit()
        data['credit'] = Account.objects.get(pk=data['id']).get_credit()
        data['balance'] = data['debit'] - data['credit']
        return data
