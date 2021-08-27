from django.urls import path
from . import views

app_name = 'wallet'
urlpatterns = [
    path('transactionlist/', views.TransactionList.as_view(), name='transaction_list'),
]
