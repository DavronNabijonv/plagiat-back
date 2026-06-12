from django.contrib import admin

from core.apps.shared.models.promo_code import PromoCode, PromoUsage


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_percent', 'valid_until',
        'max_uses', 'used_count', 'is_active',
    )
    list_filter = ('is_active',)
    search_fields = ('code',)
    readonly_fields = ('used_count',)


@admin.register(PromoUsage)
class PromoUsageAdmin(admin.ModelAdmin):
    list_display = ('promo', 'order', 'user', 'discount_amount', 'created_at')
    readonly_fields = ('promo', 'order', 'user', 'discount_amount')
    ordering = ('-created_at',)
