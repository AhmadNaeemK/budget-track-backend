from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

phone_regex = RegexValidator(regex=r'^\+{1}?\d{9,15}$',
                             message="Phone number must be entered in the format:" +
                                     " '+999999999'. Up to 15 digits allowed.")


class EmailAuthenticatedUser(AbstractUser):
    email = models.EmailField(unique=True)
    friends = models.ManyToManyField("EmailAuthenticatedUser", blank=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    display_picture = models.ImageField(blank=True, upload_to='display_pictures/')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class FriendRequest(models.Model):
    user = models.ForeignKey(to=EmailAuthenticatedUser,
                             related_name='Sender',
                             on_delete=models.CASCADE)
    receiver = models.ForeignKey(to=EmailAuthenticatedUser,
                                 related_name='Receiver',
                                 on_delete=models.CASCADE)
    request_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'receiver']
