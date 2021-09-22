from django.contrib import admin

from .models import Transaction, CashAccount, ScheduledTransaction


class TransactionAdminInline(admin.TabularInline):
    model = Transaction
    extra = 2


class CashAccountsAdminInline(admin.TabularInline):
    model = CashAccount
    extra = 1


class CashAccountsAdmin(admin.ModelAdmin):
    inlines = [TransactionAdminInline]
    list_display = ('title', 'user', 'balance', 'limit', 'creation_time', 'get_expenses')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'transaction_time', 'amount')


class ScheduledTransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'scheduled_time', 'amount')


admin.site.register(CashAccount, CashAccountsAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(ScheduledTransaction, ScheduledTransactionAdmin)
