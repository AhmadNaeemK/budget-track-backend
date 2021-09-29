from django.db import models
from django.contrib.auth.models import AbstractUser


class EmailAuthenticatedUser(AbstractUser):
    email = models.EmailField(unique=True)
    friends = models.ManyToManyField("EmailAuthenticatedUser", blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class FriendRequest(models.Model):

    user = models.ForeignKey(to=EmailAuthenticatedUser, related_name='Sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(to=EmailAuthenticatedUser, related_name='Receiver', on_delete=models.CASCADE)
    request_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'receiver']
