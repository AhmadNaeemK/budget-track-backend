from django.urls import path
from . import views

app_name= 'wallet'
urlpatterns = [
    path('transactions/', views.TransactionList, name='post_list'),
]
