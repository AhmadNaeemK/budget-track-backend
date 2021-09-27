from django.contrib import admin
from .models import MyUser, FriendRequest
from django.contrib.auth.admin import UserAdmin


class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'receiver', 'request_time']


admin.site.register(MyUser, UserAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)