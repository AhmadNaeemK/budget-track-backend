from django.contrib import admin
from .models import MyUser
from django.contrib.auth.admin import UserAdmin

admin.site.register(MyUser, UserAdmin)

