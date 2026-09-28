from django.contrib import admin
from .models import CustomUser

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role' )
    list_filter = ('role',)
    # search_fields = ('username', 'email', 'first_name', 'last_name')
    # ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)