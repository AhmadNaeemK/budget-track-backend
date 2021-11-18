from django.contrib import admin

from .models import Transaction, CashAccount, SplitTransaction


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
    list_display = ('title', 'user', 'cash_account', 'category', 'transaction_time', 'amount',
                    'scheduled', 'split_expense')


class SplitTransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'category', 'paying_friend', 'get_friends_in_split')

    def get_friends_in_split(self, obj):
        return "\n".join([user.username for user in obj.get_all_friends_involved()])



admin.site.register(CashAccount, CashAccountsAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(SplitTransaction, SplitTransactionAdmin)
