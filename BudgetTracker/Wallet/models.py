from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_tracking_date = models.DateField()
    gross_income = models.FloatField()
    gross_expenses = models.FloatField()

    @admin.display(
        description='Balance'
    )
    def calc_balance(self):
        return self.gross_income - self.gross_expenses


class Accounts(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    account_category_choices = [
        ('HealthCare', 'Doctor/Medicine'),
        ('Loans/Interests', 'Loans/Interests'),
        ('Travel', 'Petrol/Transport'),
        ('Cash', 'Money')
        ]

    category = models.TextField(choices=account_category_choices)
    amount = models.FloatField()


class Transactions(models.Model):
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    amount = models.FloatField()
    debit = models.BooleanField()

    def save(self, *args, **kwargs):
        if self.debit:
            self.account.wallet.gross_income += self.amount
            self.account.amount += self.amount
        else:
            self.account.wallet.gross_expenses += self.amount
            self.account.amount -= self.amount

        self.account.save()
        self.account.wallet.save()
        super(Transactions, self).save(*args, **kwargs)

