from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from core import models


class CustomUserCreateForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'phone_number')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'phone_number')


class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreateForm
    form = CustomUserChangeForm
    ordering = ['id']
    list_display = ('email', 'name',)
    list_filter = ('email', 'name',)
    fieldsets = (
        (None, {'fields': ['email', 'password', 'phone_number']}),
        ('Personal Info', {'fields': ['name']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser']}),
        ('Important Dates', {'fields': ['last_login']})
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': ('email', 'name', 'password1', 'password2', 'phone_number', 'is_staff', 'is_active', 'is_superuser')
        }),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Organization)
admin.site.register(models.Project)
admin.site.register(models.ProjectContributor)
admin.site.register(models.ActivityEntry)
