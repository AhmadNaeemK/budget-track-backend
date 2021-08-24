from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('list/', views.UserList.as_view()),
    path('register/', views.RegisterUser.as_view()),
    path('login/', views.LoginUser.as_view()),
    path('logout/', views.User_logout),
]
