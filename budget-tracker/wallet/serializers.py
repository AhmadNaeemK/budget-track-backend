from rest_framework import serializers

from django.conf import settings

from .models import Transaction, CashAccount

import datetime
import pytz


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

    def validate(self, data):

        def get_from_request_or_instance(attr_name):
            if attr_name in data:
                return data[attr_name]
            if self.instance and hasattr(self.instance, attr_name):
                return getattr(self.instance, attr_name)
            return None

        cash_account = get_from_request_or_instance('cash_account')
        amount = get_from_request_or_instance('amount')
        category = get_from_request_or_instance('category')
        if (category != Transaction.Categories.Income.value and cash_account.limit != 0 and
                (amount >= cash_account.limit or amount >= cash_account.balance)):
            raise serializers.ValidationError('You are exceeding your budget')

        if category != Transaction.Categories.Income.value and amount > cash_account.balance:
            raise serializers.ValidationError("Cash Account does not have enough Balance")

        if self.partial:
            if category != Transaction.Categories.Income.value:
                if self.instance and self.instance.cash_account.balance + self.instance.amount < amount:
                    raise serializers.ValidationError("Cash Account does not have enough Balance")
            else:
                if (self.instance and self.instance.cash_account.balance - self.instance.amount + amount <
                        self.instance.cash_account.get_expenses()):
                    raise serializers.ValidationError("Expenses Increase the new Balance")

        return data


class CashAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashAccount
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['expenses'] = instance.get_expenses()
        return data


class ScheduledTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'category', 'title', 'cash_account', 'transaction_time', 'scheduled']

    def validate(self, data):
        curr_time_zone = pytz.timezone(settings.TIME_ZONE)
        if data.get('transaction_time') <= datetime.datetime.now(tz=curr_time_zone):
            raise serializers.ValidationError('Date and Time can not be less than previous date')

        return data
