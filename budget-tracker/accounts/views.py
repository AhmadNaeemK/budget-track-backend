from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework import authentication, permissions

from django.contrib.auth.models import User

from .serializers import UserSerializer, RegistrationSerializer, LoginSerializer

# Create your views here.


class UserList(APIView):

    permission_classes = [permissions.AllowAny]
    def get(self, request):
        print(request.user)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


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


class LoginUser(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            print(request.user)
            return Response({
                'user': UserSerializer(user).data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutUser(APIView):

    def get(self, request):
        print(request.user.auth_token)
        return Response('User Logged Out')

