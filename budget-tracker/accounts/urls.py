from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'accounts'
urlpatterns = [
    path('list/', views.UserList.as_view(), name='user_list'),
    path('<int:pk>/', views.UserRetrieveView.as_view(), name='retrieve_user'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('logout/', views.LogoutUser.as_view(), name='logout'),
    path('token/', views.MyTokenObtainPairView.as_view(), name='token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('sentFriendRequestList/', views.SentFriendRequestListView.as_view(), name='sent_friend_request_list'),
    path('receivedFriendRequestList/', views.ReceivedFriendRequestListView.as_view(),
         name='received_friend_request_list'),
    path('friendRequest/<int:pk>', views.FriendRequestView.as_view(), name='friend_request'),
    path('acceptRequest/<int:pk>', views.AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path('removeFriend/<int:pk>', views.RemoveFriendView.as_view(), name='remove_friend'),
    path('friendsList/', views.FriendsListView.as_view(), name='friends_list'),
    path('displayPicture/', views.DisplayPictureView.as_view(), name='display_picture')
]
