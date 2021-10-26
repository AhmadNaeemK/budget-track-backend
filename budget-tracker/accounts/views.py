from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import generics, status

from django.db.models import Q
from django.template.loader import render_to_string

from .models import EmailAuthenticatedUser as User, FriendRequest

from rest_framework import filters

from .filters import UserFilterBackend, ReceiverFilterBackend
from .serializers import UserSerializer, RegistrationSerializer, MyTokenObtainPairSerializer, FriendRequestSerializer

from .services import send_friend_request_sms, send_friend_request_email, send_friend_request_notification

from rest_framework_simplejwt.views import TokenObtainPairView


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserList(generics.ListAPIView):
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username']

    def get_queryset(self):
        users = User.objects.exclude(id=self.request.user.id)
        sent_friend_request_list = [req.receiver.id for req in FriendRequest.objects.filter(user=self.request.user.id)]
        received_friend_request_list = [req.user.id for req in
                                        FriendRequest.objects.filter(receiver=self.request.user.id)]
        friends_list = [friend.id for friend in User.objects.get(pk=self.request.user.id).friends.all()]
        unsent_request_users = users.exclude(
            Q(id__in=sent_friend_request_list + received_friend_request_list + friends_list))
        return unsent_request_users.order_by('username')


class RegisterUser(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data,
                'status': status.HTTP_201_CREATED,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutUser(APIView):

    def get(self, request):
        print(request.user)
        return Response('User Logged Out')


class SentFriendRequestListView(generics.ListCreateAPIView):
    queryset = FriendRequest.objects.all().order_by('request_time')
    filter_backends = [UserFilterBackend]
    serializer_class = FriendRequestSerializer

    def perform_create(self, serializer):
        friend_request = serializer.save()
        send_friend_request_sms(friend_request)
        send_friend_request_email(friend_request)
        send_friend_request_notification(friend_request)


class ReceivedFriendRequestListView(generics.ListAPIView):
    queryset = FriendRequest.objects.all().order_by('request_time')
    filter_backends = [ReceiverFilterBackend]
    serializer_class = FriendRequestSerializer


class FriendRequestView(generics.RetrieveDestroyAPIView):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer


class AcceptFriendRequestView(APIView):

    def get(self, request, pk):
        friend_request = FriendRequest.objects.get(pk=pk)
        if friend_request.receiver.id == request.user.id:
            friend_request.user.friends.add(friend_request.receiver)
            friend_request.receiver.friends.add(friend_request.user)
            friend_request.delete()
            return Response('Request Accepted', status=status.HTTP_201_CREATED)
        else:
            return Response('Request Not Accepted', status=status.HTTP_400_BAD_REQUEST)


class RemoveFriendView(APIView):

    def get(self, request, pk):
        user = User.objects.get(pk=request.user.id)
        friend_to_be_removed = user.friends.get(pk=pk)
        try:
            user.friends.remove(friend_to_be_removed)
            friend_to_be_removed.friends.remove(user)
            return Response('Friend Removed', status=status.HTTP_204_NO_CONTENT)
        except:
            return Response('Could not Remove Friend', status=status.HTTP_400_BAD_REQUEST)


class FriendsListView(generics.ListAPIView):
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username']

    def get_queryset(self):
        user = User.objects.get(pk=self.request.user.id)
        friends = user.friends.all().order_by('username')
        return friends
