from django.contrib import admin


from .models import Transactions, Accounts, Wallet
# Register your models here.


class TransactionAdminInline(admin.TabularInline):
    model = Transactions
    extra = 2


class AccountsAdminInline(admin.TabularInline):
    model = Accounts
    extra = 1


class WalletAdmin(admin.ModelAdmin):
    inlines = [AccountsAdminInline]
    list_display = ('user', 'start_tracking_date', 'calc_balance')


class AccountsAdmin(admin.ModelAdmin):
    inlines = [TransactionAdminInline]
    list_display = ('title', 'wallet', 'category', 'amount')


admin.site.register(Wallet, WalletAdmin)
admin.site.register(Accounts, AccountsAdmin)
