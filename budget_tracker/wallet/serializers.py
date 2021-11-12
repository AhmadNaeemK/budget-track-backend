from rest_framework import serializers

from django.conf import settings

from .models import Transaction, CashAccount, SplitTransaction, TransactionCategories
from .utils import SplitTransactionUtils

from accounts.models import EmailAuthenticatedUser
from accounts.serializers import UserSerializer

import datetime
import pytz


class CashAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashAccount
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['expenses'] = instance.get_expenses()
        return data


class SplitTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitTransaction
        fields = ['id', 'title', 'category', 'total_amount', 'creator', 'paying_friend', 'all_friends_involved']

    creator = UserSerializer(read_only=True)
    paying_friend = UserSerializer(read_only=True)
    all_friends_involved = UserSerializer(many=True, read_only=True)

    def create(self, validated_data):
        validated_data['creator'] = EmailAuthenticatedUser.objects.get(pk=self.initial_data.get('creator'))
        validated_data['paying_friend'] = EmailAuthenticatedUser.objects.get(pk=self.initial_data.get('paying_friend'))
        split = SplitTransaction.objects.create(**validated_data)
        friends_involved = EmailAuthenticatedUser.objects.filter(
            pk__in=[int(friend_id) for friend_id in self.initial_data.get('all_friends_involved')])
        split.all_friends_involved.set(friends_involved)
        return split

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get('request'):
            payable, required, paid = SplitTransactionUtils.get_user_payable_amount(self.context.get('request').user.id, instance)
            data['completed_payment'] = paid >= required
        for friend in data['all_friends_involved']:
            payable, required, paid = SplitTransactionUtils.get_user_payable_amount(friend['id'], instance)
            friend['payable'] = payable
            friend['required'] = required
            friend['paid'] = paid
        data['category'] = TransactionCategories.choices[data['category']]
        return data


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'category', 'transaction_time', 'cash_account', 'scheduled', 'title',
                  'split_expense', ]

    user = UserSerializer(read_only=True)
    split_expense = SplitTransactionSerializer(read_only=True)
    cash_account = CashAccountSerializer(read_only=True)

    def create(self, validated_data):
        validated_data['cash_account'] = CashAccount.objects.get(pk=self.initial_data.get('cash_account'))
        validated_data['user'] = EmailAuthenticatedUser.objects.get(pk=self.initial_data.get('user'))
        if self.initial_data.get('split_expense'):
            validated_data['split_expense'] = SplitTransaction.objects.get(pk=self.initial_data.get('split_expense'))
        transaction = Transaction.objects.create(**validated_data)
        return transaction

    def validate(self, data):

        def get_from_request_or_instance(attr_name):
            if attr_name in data:
                return data[attr_name]
            if self.instance and hasattr(self.instance, attr_name):
                return getattr(self.instance, attr_name)
            return None

        cash_account = get_from_request_or_instance('cash_account') or CashAccount.objects.get(pk=self.initial_data.get('cash_account'))
        amount = get_from_request_or_instance('amount')
        category = get_from_request_or_instance('category')
        if (category != TransactionCategories.Income.value and cash_account.limit != 0 and
                (cash_account.get_expenses() + amount > cash_account.limit)):
            raise serializers.ValidationError('You are exceeding your budget')

        if not self.partial and category != TransactionCategories.Income.value and amount > cash_account.balance:
            raise serializers.ValidationError("Cash Account does not have enough Balance")

        if self.partial:
            if category != TransactionCategories.Income.value:
                if self.instance and self.instance.cash_account.balance + self.instance.amount < amount:
                    raise serializers.ValidationError("Cash Account does not have enough Balance")
            else:
                if (self.instance and self.instance.cash_account.balance - self.instance.amount + amount <
                        self.instance.cash_account.get_expenses()):
                    raise serializers.ValidationError("Expenses Increase the new Balance")

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = TransactionCategories.choices[data['category']]
        return data


class ScheduledTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'category', 'title', 'cash_account', 'transaction_time', 'scheduled']

    user = UserSerializer(read_only=True)
    cash_account = CashAccountSerializer(read_only=True)

    def create(self, validated_data):
        validated_data['user'] = EmailAuthenticatedUser.objects.get(pk=self.initial_data.get('user'))
        validated_data['cash_account'] = CashAccount.objects.get(pk=self.initial_data.get('cash_account'))
        transaction = Transaction.objects.create(**validated_data)
        return transaction

    def validate(self, data):
        curr_time_zone = pytz.timezone(settings.TIME_ZONE)
        if data.get('transaction_time') <= datetime.datetime.now(tz=curr_time_zone):
            raise serializers.ValidationError('Date and Time can not be less than previous date')

        return data


class MaxSplitsDueSerializer(serializers.Serializer):
    payable_amount = serializers.IntegerField()
    split = SplitTransactionSerializer(read_only=True)
