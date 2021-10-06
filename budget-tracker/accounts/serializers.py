from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import EmailAuthenticatedUser as User, FriendRequest
from wallet.models import CashAccount


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}, 'username': {'required': True, 'allow_blank': False}}

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data['username'], validated_data['email'], validated_data['password'])
        cashAccount = CashAccount.objects.create(title='Cash', user=user)
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['name'] = user.username
        token['email'] = user.email

        return token

    def validate(self, attrs):
        # The default result (access/refresh tokens)
        data = super(MyTokenObtainPairSerializer, self).validate(attrs)
        # Custom data you want to include
        data.update({'user': self.user.username})
        data.update({'id': self.user.id})
        # and everything else you want to send in the response
        return data


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = '__all__'
    user = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    def validate(self, data):

        if data['user'] == data['receiver']:
            raise serializers.ValidationError("Request Sender and Receiver cannot be same")

        if data['receiver'] in data['user'].friends.all():
            raise serializers.ValidationError("Already Friends")

        return data

    def create(self, validated_data):
        validated_data['user'] = User.objects.get(pk=self.initial_data.get('user'))
        validated_data['receiver'] = User.objects.get(pk=self.initial_data.get('receiver'))
        request = FriendRequest.objects.create(**validated_data)
        return request

