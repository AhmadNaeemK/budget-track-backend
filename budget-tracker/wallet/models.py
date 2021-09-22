from django.db import models
from django.contrib import admin
from django.conf import settings


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
        transactions = Transaction.objects.filter(cash_account=self).exclude(category=Transaction.Categories.Income)
        expenses = [transaction.amount for transaction in transactions]
        return sum(expenses)


class Transaction(models.Model):
    title = models.CharField(max_length=120)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cash_account = models.ForeignKey(to=CashAccount, on_delete=models.CASCADE)
    transaction_time = models.DateTimeField(auto_now=True)

    class Categories (models.IntegerChoices):
        Income = 0
        Drink = 1
        Fuel = 2
        HealthCare = 3
        Travel = 4
        Food = 5
        Grocery = 6
        Other = 7

    category = models.IntegerField(choices=Categories.choices)
    amount = models.IntegerField(default=0)


class ScheduledTransaction(models.Model):
    title = models.CharField(max_length=120)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cash_account = models.ForeignKey(to=CashAccount, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()

    category = models.IntegerField(choices=Transaction.Categories.choices)
    amount = models.IntegerField(default=0)
