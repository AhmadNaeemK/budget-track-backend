from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import EmailAuthenticatedUser, FriendRequest


class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'receiver', 'request_time']


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'phone_number', 'is_staff', 'last_login']


admin.site.register(EmailAuthenticatedUser, CustomUserAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)
