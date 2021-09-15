from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import generics

from .models import MyUser as User

from wallet.models import Wallet

from .serializers import UserSerializer, RegistrationSerializer, MyTokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenObtainPairView

from datetime import datetime


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserList(generics.ListAPIView):

    serializer_class = UserSerializer

    def get_queryset(self):
        users = User.objects.all()
        return users

    def list(self, request):
        users = self.get_queryset()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class RegisterUser(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            wallet = Wallet(user=user, start_tracking_date=datetime.now())
            wallet.save()
            return Response({
                'user': UserSerializer(user).data,
                'status': status.HTTP_201_CREATED,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutUser(APIView):

    def get(self, request):
        print(request.user)
        return Response('User Logged Out')
