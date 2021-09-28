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
    list_display = ('title', 'user', 'category', 'transaction_time', 'amount', 'scheduled')


class SplitTransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'category', 'get_users_in_split', 'get_payed_users', 'total_amount')

    def get_users_in_split(self, obj):
        return "\n".join([user.username for user in obj.users_in_split.all()])
    def get_payed_users(self, obj):
        return "\n".join([user.username for user in obj.payed_users.all()])


admin.site.register(CashAccount, CashAccountsAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(SplitTransaction, SplitTransactionAdmin)
