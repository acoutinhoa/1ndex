from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(User, UserAdmin)
admin.site.register(Grupo)
admin.site.register(Url)
admin.site.register(Convite)

