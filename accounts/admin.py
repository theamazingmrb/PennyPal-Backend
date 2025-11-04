
from django.contrib import admin
from .models import Profile, Category, Transaction


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    search_fields = ("user__username", "user__email")


admin.site.register(Category)
admin.site.register(Transaction)
