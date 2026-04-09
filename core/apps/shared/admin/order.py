from django.contrib import admin

from core.apps.shared.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'created_at')
    list_filter = ('type', 'created_at')
    ordering = ('-created_at',)
