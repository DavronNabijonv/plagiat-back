from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from core.apps.shared.models.card_transfer import CardRequisite, CardTransferPayment
from core.apps.shared.utils.telegram import send_telegram_message


@admin.register(CardRequisite)
class CardRequisiteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'country', 'currency', 'card_number',
        'card_holder', 'bank_name', 'exchange_rate', 'is_active',
    )
    list_filter = ('is_active', 'currency')
    search_fields = ('country', 'card_number', 'card_holder')


@admin.register(CardTransferPayment)
class CardTransferPaymentAdmin(admin.ModelAdmin):
    """
    AD-01: chek tasdiqlash navbati. Bir-ikki bosishda tasdiqlash/rad etish
    (actions), chek rasmi preview, audit (reviewed_by/at + izoh).
    """
    list_display = (
        'id', 'user', 'order', 'amount', 'currency',
        'state', 'receipt_preview', 'created_at', 'reviewed_by',
    )
    list_filter = ('state', 'currency')
    search_fields = ('user__phone', 'order__id')
    readonly_fields = (
        'order', 'user', 'requisite', 'receipt', 'receipt_preview',
        'amount', 'currency', 'reviewed_by', 'reviewed_at',
    )
    actions = ['approve_payments', 'reject_payments']

    @admin.display(description="Chek")
    def receipt_preview(self, obj):
        if not obj.receipt:
            return "—"
        url = obj.receipt.url
        if url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height:60px"/></a>',
                url, url,
            )
        return format_html('<a href="{}" target="_blank">Faylni ochish</a>', url)

    def _notify_user(self, payment, approved: bool):
        """BE-25: tasdiqlangach foydalanuvchiga xabar boradi."""
        tg_id = payment.user.tg_id
        if not tg_id:
            return
        if approved:
            text = (
                "✅ To'lovingiz tasdiqlandi!\n"
                f"Buyurtma №{payment.order_id} — natija va sertifikat ochildi."
            )
        else:
            izoh = f"\nIzoh: {payment.admin_comment}" if payment.admin_comment else ""
            text = (
                "❌ To'lov cheki rad etildi.\n"
                f"Buyurtma №{payment.order_id}.{izoh}\n"
                "Iltimos, to'g'ri chek bilan qayta urinib ko'ring."
            )
        send_telegram_message(tg_id, text)

    @admin.action(description="✅ Tanlangan to'lovlarni tasdiqlash")
    def approve_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(state=CardTransferPayment.PENDING):
            payment.state = CardTransferPayment.APPROVED
            payment.reviewed_by = request.user
            payment.reviewed_at = timezone.now()
            payment.save(update_fields=['state', 'reviewed_by', 'reviewed_at'])

            order = payment.order
            order.payment_provider = 'card_transfer'
            order.save(update_fields=['payment_provider'])

            self._notify_user(payment, approved=True)
            count += 1
        self.message_user(request, f"{count} ta to'lov tasdiqlandi.")

    @admin.action(description="❌ Tanlangan to'lovlarni rad etish")
    def reject_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(state=CardTransferPayment.PENDING):
            payment.state = CardTransferPayment.REJECTED
            payment.reviewed_by = request.user
            payment.reviewed_at = timezone.now()
            payment.save(update_fields=['state', 'reviewed_by', 'reviewed_at'])
            self._notify_user(payment, approved=False)
            count += 1
        self.message_user(request, f"{count} ta to'lov rad etildi.")
