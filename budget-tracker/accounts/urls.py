from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'accounts'
urlpatterns = [
    path('list/', views.UserList.as_view(), name='user_list'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('logout/', views.LogoutUser.as_view(), name='logout'),
    path('token/', views.MyTokenObtainPairView.as_view(), name='token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh')
]
