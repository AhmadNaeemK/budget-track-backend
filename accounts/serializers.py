from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import EmailAuthenticatedUser as User, FriendRequest


class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source='get_full_name')
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'display_picture', 'first_name',
                  'last_name', 'fullname']


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'phone_number', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True},
                        'username': {'required': True, 'allow_blank': False},
                        'phone_number': {'required': True},
                        'first_name': {'required': True, 'allow_blank': False},
                        'last_name': {'required': True, 'allow_blank': False}
                        }

    def create(self, validated_data):
        user = User(**validated_data)
        user.is_active = False
        user.set_password(validated_data['password'])
        user.save()
        return user


class ValidateTokenPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # The default result (access/refresh tokens)
        data = super().validate(attrs)
        # Custom data you want to include
        data.update({'user': UserSerializer(self.user).data})
        # and everything else you want to send in the response
        return data


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = '__all__'

    user = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    def validate(self, attrs):

        user = User.objects.get(pk=self.initial_data.get('user'))
        receiver = User.objects.get(pk=self.initial_data.get('receiver'))
        if user == receiver:
            raise serializers.ValidationError("Request Sender and Receiver cannot be same")

        if receiver in user.friends.all():
            raise serializers.ValidationError("Already Friends")

        return attrs

    def create(self, validated_data):
        validated_data['user'] = User.objects.get(pk=self.initial_data.get('user'))
        validated_data['receiver'] = User.objects.get(pk=self.initial_data.get('receiver'))
        request = FriendRequest.objects.create(**validated_data)
        return request
