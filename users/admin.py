from django.contrib import admin
from django.contrib.auth import get_user_model


User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_washer', 'is_staff', 'is_active')
    list_filter = ('is_washer', 'is_staff', 'is_active')
    search_fields = ('email',)
    readonly_fields = ('last_login',)
    list_display_links = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Статус', {'fields': ('is_washer', 'is_staff', 'is_active')}),
        ('Даты', {'fields': ('last_login',)}),
    )
