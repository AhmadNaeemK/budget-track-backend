from django.db import models
from django.contrib import admin
from django.conf import settings


class Wallet(models.Model):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_tracking_date = models.DateField()

    def save(self, *args, **kwargs):
        # on creation of wallet
        if not self.pk:
            cash = Account(wallet=self, title='Cash', category='Cash')
            super(Wallet, self).save(*args, **kwargs)
            cash.save()
        else:
            super(Wallet, self).save(*args,**kwargs)

    @admin.display(
        description='Balance'
    )
    def get_balance(self):
        accounts = Account.objects.filter(wallet=self)
        balance = 0
        for account in accounts:
            balance += account.get_balance()
        return balance

    @admin.display(description='Remaining Cash')
    def get_cash_balance(self):
        cash_accounts = Account.objects.filter(wallet=self, category='Cash')
        remaining_cash = 0
        for account in cash_accounts:
            remaining_cash += account.get_balance()
        if remaining_cash < 0:
            print('You have negative cash flow, ', remaining_cash)
        return remaining_cash


class Account(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    account_category_choices = [
        ('HealthCare', 'Doctor/Medicine'),
        ('Loans/Interests', 'Loans/Interests'),
        ('Travel', 'Petrol/Transport'),
        ('Cash', 'Cash/Bank/'),
        ('Lifestyle', 'Grocery/Sports'),
        ('Food', 'Restaurant/Fast Food'),
        ('Salary', 'Salary/Profit/Income'),
        ('Other', 'Other')
        ]
    category = models.TextField(choices=account_category_choices)

    debit_amount = models.FloatField(default=0)
    credit_amount = models.FloatField(default=0)

    def get_debit(self):
        d_amount = 0
        transactions = Transaction.objects.filter(debit_account=self)
        for transaction in transactions:
            d_amount += transaction.amount
        return d_amount

    def get_credit(self):
        c_amount = 0
        transactions = Transaction.objects.filter(credit_account=self)
        for transaction in transactions:
            c_amount += transaction.amount
        return c_amount

    def get_balance(self):
        self.debit_amount = self.get_debit()
        self.credit_amount = self.get_credit()
        return self.get_debit() - self.get_credit()

    def update_account(self):
        self.credit_amount = self.get_credit()
        self.debit_amount = self.get_debit()
        self.save()

    @admin.display(description='User')
    def get_user(self):
        return self.wallet.user

    @admin.display(description='Wallet_id')
    def get_wallet_id(self):
        return self.wallet.id

    @admin.display(description='Balance')
    def get_balance(self):
        return self.debit_amount - self.credit_amount

    class Meta:
        unique_together = [['wallet', 'title']]


class Transaction(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    debit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debit_account')
    credit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='credit_account')
    transaction_date = models.DateTimeField(auto_now=True)
    amount = models.FloatField()

    def save(self, *args, **kwargs):
        super(Transaction, self).save(*args, **kwargs)
        self.debit_account.update_account()
        self.credit_account.update_account()

    @admin.display(description='Credit Account')
    def get_credit_account(self):
        return self.credit_account.title

    @admin.display(description='Debit Account')
    def get_debit_account(self):
        return self.debit_account.title

