from django.contrib import admin

from .models import Transaction, Account, Wallet


class TransactionAdminInline(admin.TabularInline):
    model = Transaction
    fk_name = 'debit_account'
    extra = 2


class AccountsAdminInline(admin.TabularInline):
    model = Account
    extra = 1


class WalletAdmin(admin.ModelAdmin):
    inlines = [AccountsAdminInline]
    list_display = ('user', 'get_balance', 'get_cash_balance', 'start_tracking_date')


class AccountsAdmin(admin.ModelAdmin):
    inlines = [TransactionAdminInline]
    list_display = ('title', 'get_wallet_id', 'get_user', 'category', 'budget_limit')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_credit_account', 'get_debit_account', 'transaction_date', 'amount')


admin.site.register(Wallet, WalletAdmin)
admin.site.register(Account, AccountsAdmin)
admin.site.register(Transaction, TransactionAdmin)