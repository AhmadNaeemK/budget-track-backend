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
    path('categoryExpenseData', views.ExpenseCategoryData.as_view(), name='category_expense_data'),
]
