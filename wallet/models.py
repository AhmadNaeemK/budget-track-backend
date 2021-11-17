from django.db import models
from django.contrib import admin
from django.conf import settings

from django.utils.timezone import now


class CashAccount(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    balance = models.IntegerField(default=0)
    limit = models.IntegerField(default=0)
    creation_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'title']

    @admin.display(description='Total Expenses')
    def get_expenses(self):
        transactions = Transaction.objects.filter(cash_account=self, scheduled=False)
        transaction_expenses = transactions.exclude(category=TransactionCategories.Income)
        expenses = [transaction.amount for transaction in transaction_expenses]
        return sum(expenses)


class TransactionCategories (models.IntegerChoices):
    Income = 0
    Drink = 1
    Fuel = 2
    HealthCare = 3
    Travel = 4
    Food = 5
    Grocery = 6
    Other = 7


class SplitTransaction (models.Model):

    title = models.CharField(max_length=120)
    category = models.IntegerField(choices=TransactionCategories.choices)
    total_amount = models.IntegerField(default=0)
    creator = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='creator')
    paying_friend = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                      on_delete=models.CASCADE,
                                      related_name='paying_user')
    all_friends_involved = models.ManyToManyField(to=settings.AUTH_USER_MODEL,
                                                  related_name='involved_friends')

    @admin.display(description="Friends Involved")
    def get_all_friends_involved(self):
        return self.all_friends_involved.all()

    @admin.display(description="Friend Who Paid")
    def get_friends_paid(self):
        return self.friends_paid.all()


class Transaction(models.Model):
    title = models.CharField(max_length=120)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cash_account = models.ForeignKey(to=CashAccount, on_delete=models.CASCADE)
    transaction_time = models.DateTimeField(default=now)
    scheduled = models.BooleanField(default=False)

    category = models.IntegerField(choices=TransactionCategories.choices)
    amount = models.IntegerField(default=0)

    split_expense = models.ForeignKey(to=SplitTransaction,
                                      on_delete=models.CASCADE,
                                      blank=True, null=True)
