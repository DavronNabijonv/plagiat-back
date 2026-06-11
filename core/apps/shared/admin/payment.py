from django.contrib import admin

from core.apps.shared.models.multicard_transaction import MulticardTransaction
from core.apps.shared.models.balance_topup import BalanceTopup


@admin.register(MulticardTransaction)
class MulticardTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'topup', 'transaction_id', 'amount', 'state', 'created_at')
    list_filter = ('state',)
    ordering = ('-created_at',)
    readonly_fields = ('transaction_id', 'order', 'topup', 'amount')


@admin.register(BalanceTopup)
class BalanceTopupAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'is_applied', 'created_at')
    list_filter = ('is_applied',)
    ordering = ('-created_at',)
    readonly_fields = ('user', 'amount', 'is_applied')
