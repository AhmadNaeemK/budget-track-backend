from django.urls import path
from . import views

app_name = 'wallet'
urlpatterns = [
    path('expenselist/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expense/<int:pk>', views.ExpenseView.as_view(), name='expense_detail'),
    path('incomelist/', views.IncomeListView.as_view(), name='income_list'),
    path('income/<int:pk>', views.IncomeView.as_view(), name='income_detail'),
    path('cashAccountList/', views.CashAccountListView.as_view(), name='cash_accounts_list'),
    path('cashAccount/<int:pk>', views.CashAccountView.as_view(), name='cash_account_detail'),
    path('transactionCategoryList/', views.TransactionCategoryChoicesList.as_view(), name='transaction_category_list'),
    path('categoryExpenseData', views.ExpenseCategoryDataView.as_view(), name='category_expense_data'),
    path('scheduledTransactionList/', views.ScheduledTransactionListView.as_view(), name='scheduled_transaction_list'),
    path('scheduledTransaction/<int:pk>', views.ScheduledTransactionView.as_view(), name='scheduled_transaction'),
    path('splitTransactionList/', views.SplitTransactionListView.as_view(), name='split_transaction_list'),
    path('splitTransaction/<int:pk>', views.SplitTransactionView.as_view(), name='split_transaction'),
    path('splitPaymentData/<int:pk>', views.SplitPaymentData.as_view(), name='split_payment_data'),
    path('paySplit/', views.PaySplit.as_view(), name='pay_split'),
    path('splitsDueMax', views.MaximumSplitsDue.as_view(), name='splits_due'),
    path('transactionsInSplit/', views.TransactionsWithSplit.as_view(), name='transactions_with_split'),
    path('monthlyTransactionChartData/', views.MonthlyTransactionDataView.as_view(),
         name='monthly_transaction_chart_data'),
]
