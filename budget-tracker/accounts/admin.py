from django.contrib import admin
from .models import MyUser
from django.contrib.auth.admin import UserAdmin


class FriendAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'friends')


admin.site.register(MyUser, UserAdmin)
