import os

import jwt
import rest_framework_simplejwt.exceptions
from django.conf import settings
from django.db.models import Q
from rest_framework import permissions, generics, status, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView

from .filters import UserFilterBackend, ReceiverFilterBackend
from .models import EmailAuthenticatedUser as User, FriendRequest
from .serializers import UserSerializer, RegistrationSerializer, \
    ValidateTokenPairSerializer, FriendRequestSerializer
from .tasks import send_friend_request_notifications, \
    send_user_verification_email_notification, send_password_recovery_email_notification


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = ValidateTokenPairSerializer


class UserList(generics.ListAPIView):
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username']

    def get_queryset(self):
        user = User.objects.prefetch_related("sender", "receiver").get(pk=self.request.user.id)
        sent_friend_request_list = [req.receiver.id for req in user.sender.all()]
        received_friend_request_list = [req.user.id for req in user.receiver.all()]
        friends_list = [friend.id for friend in user.friends.all()]
        unsent_request_users = User.objects.exclude(
            Q(id__in=sent_friend_request_list + received_friend_request_list + friends_list + [
                self.request.user.id]))
        return unsent_request_users.order_by('username')


class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()


class RegisterUser(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user = User.objects.get(pk=user.id)
            send_user_verification_email_notification.delay(user.id)
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
        serializer.save()
        send_friend_request_notifications.delay(serializer.data)


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
        user.friends.remove(friend_to_be_removed)
        friend_to_be_removed.friends.remove(user)
        return Response('Friend Removed', status=status.HTTP_204_NO_CONTENT)


class FriendsListView(generics.ListAPIView):
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username']

    def get_queryset(self):
        user = User.objects.get(pk=self.request.user.id)
        friends = user.friends.all().order_by('username')
        return friends


class DisplayPictureView(generics.GenericAPIView):
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = User.objects.get(pk=request.user.id)
        if user.display_picture:
            os.remove(settings.MEDIA_ROOT + f'/{user.display_picture.name}')
            user.display_picture = None
        user.display_picture = request.FILES.get('display_picture')
        user.save()
        return Response("Display Picture Updated", status=status.HTTP_202_ACCEPTED)


class VerifyUserView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.GET.get('token')
        try:
            validated_token = JWTTokenUserAuthentication().get_validated_token(token)
            user = User.objects.get(pk=validated_token.payload.get('user_id'))
            user.is_active = True
            user.save()
            return Response('User Verified', status=status.HTTP_200_OK)

        except rest_framework_simplejwt.exceptions.InvalidToken:
            payload = jwt.decode(jwt=token,
                                 key=settings.SIMPLE_JWT['SIGNING_KEY'],
                                 algorithms=[settings.SIMPLE_JWT['ALGORITHM']],
                                 options={"verify_signature": False})
            send_user_verification_email_notification.delay(payload.get('user_id'))
            return Response('Unable to verify', status=status.HTTP_400_BAD_REQUEST)


class VerificationLinkRegeneration(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            user = User.objects.get(email=request.GET.get('email'))
            send_user_verification_email_notification.delay(user.id)
            return Response('Verification mail sent', status=status.HTTP_200_OK)
        except User.DoesNotExist as exception:
            return Response(exception, status=status.HTTP_400_BAD_REQUEST)


class UpdatePasswordView(generics.GenericAPIView):

    def post(self, request):
        try:
            user = User.objects.get(pk=request.user.id)
            user.set_password(request.data.get('password'))
            user.save()
            return Response('Password Reset', status=status.HTTP_200_OK)
        except User.DoesNotExist as exception:
            return Response(exception, status=status.HTTP_400_BAD_REQUEST)


class PasswordRecoveryLinkGeneration(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            user = User.objects.get(email=request.GET.get('email'))
            send_password_recovery_email_notification.delay(user.id)
            return Response('Verification mail sent', status=status.HTTP_200_OK)
        except User.DoesNotExist as exception:
            return Response(exception, status=status.HTTP_400_BAD_REQUEST)
