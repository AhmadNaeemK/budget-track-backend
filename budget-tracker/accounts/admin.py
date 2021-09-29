from django.contrib import admin
from .models import EmailAuthenticatedUser, FriendRequest
from django.contrib.auth.admin import UserAdmin


class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'receiver', 'request_time']


admin.site.register(EmailAuthenticatedUser, UserAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)