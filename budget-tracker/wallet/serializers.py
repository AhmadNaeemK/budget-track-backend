from rest_framework import serializers

from .models import Transaction, Account


class TransactionSerializer (serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'title', 'description', 'user', 'credit_account', 'debit_account', 'transaction_date', 'amount',]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['credit_account'] = Account.objects.get(pk=data['credit_account']).title
        data['debit_account'] = Account.objects.get(pk=data['debit_account']).title
        return data

    def validate(self, data):

        if 'credit_account' in data.keys():
            if data.get('credit_account').category not in ['Cash', 'Salary']:
                raise serializers.ValidationError("Credit Account can only be a Cash or Salary type account")

            if 'debit_account' in data.keys():
                if data.get('credit_account') == data.get('debit_account'):
                    raise serializers.ValidationError("Credit Account can not be same as debit account")
            else:
                if data.get('credit_account') == self.instance.debit_account:
                    raise serializers.ValidationError("Credit Account can not be same as debit account")

            if 'amount' in data.keys():
                if (data.get('amount') > data.get('credit_account').get_balance()
                        and data.get('credit_account').category != 'Salary'):
                    raise serializers.ValidationError("Credit Account does not have enough Balance")
            else:
                if self.instance.amount > data.get('credit_account').get_balance():
                    raise serializers.ValidationError("Credit Account does not have enough Balance")

        if 'debit_account' in data.keys():
            if data.get('debit_account').category == 'Salary':
                raise serializers.ValidationError("Debit Account can not be a Salary type account")

            if self.instance and self.instance.credit_account == data.get('debit_account'):
                raise serializers.ValidationError("Credit Account can not be same as debit account")

        if 'amount' in data.keys():
            if self.instance and self.instance.credit_account.get_balance() + self.instance.amount < data.get('amount'):
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