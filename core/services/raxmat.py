"""Multicard to'lov tizimi bilan ishlovchi service.

Token olish, invoice yaratish va callback imzosini tekshirish shu yerda
markazlashtirilgan — view'lar Multicard API tafsilotlarini bilmaydi.
"""

import hashlib
import hmac
import logging
from decimal import Decimal

from django.conf import settings

import requests

logger = logging.getLogger(__name__)


class RaxmatError(Exception):
    """Multicard API bilan ishlashda yuz bergan xatolik."""


class RaxmatService:
    """Multicard REST API mijozi (mesh API v1)."""

    # Multicard javob bermay qolsa so'rov osilib qolmasligi uchun
    REQUEST_TIMEOUT = 10

    def __init__(self) -> None:
        self.application_id = settings.MULTICARD_APPLICATION_ID
        self.secret = settings.MULTICARD_SECRET_KEY
        self.store_id = settings.MULTICARD_STORE_ID
        self.base_url = settings.MULTICARD_API_URL
        self.callback_url = settings.MULTICARD_CALLBACK_URL

    # ---------- API chaqiruvlari ----------

    def get_token(self) -> str:
        """POST /auth → JWT token.

        Har chaqiruvda yangi token olinadi (token 24 soat amal qiladi).
        """
        data = self._post(
            "/auth",
            {"application_id": self.application_id, "secret": self.secret},
        )
        token = data.get("token")
        if not token:
            raise RaxmatError("Multicard auth javobida token kelmadi")
        return token

    def create_invoice(self, amount, invoice_id, return_url: str) -> tuple[str, str]:
        """POST /payment/invoice → (uuid, checkout_url) qaytaradi.

        amount — so'mda (Decimal/int); Multicard'ga tiyinda yuboriladi.
        invoice_id — bizning tarafdagi identifikator (order.id yoki "topup_<id>").
        return_url — to'lovdan keyin foydalanuvchi qaytariladigan sahifa.
        """
        token = self.get_token()
        payload = {
            "store_id": self.store_id,
            "amount": self.to_tiyin(amount),
            "invoice_id": str(invoice_id),
            "lang": "uz",
            "return_url": return_url,
            "callback_url": self.callback_url,
        }
        data = self._post(
            "/payment/invoice",
            payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        invoice = data.get("data") or {}
        checkout_url = invoice.get("checkout_url") or invoice.get("url")
        if not checkout_url:
            raise RaxmatError(f"Multicard invoice javobida checkout_url yo'q: {data}")
        return invoice.get("uuid") or str(invoice_id), checkout_url

    # ---------- Callback imzosi ----------

    def verify_callback_sign(self, data: dict) -> bool:
        """Webhook/callback'dagi `sign` maydonini tekshiradi.

        Hujjatda SHA1(uuid + invoice_id + amount + secret) deyilgan, lekin
        amalda ayrim muhitlarda MD5(store_id + invoice_id + amount + secret)
        kelishi kuzatilgan — shu sababli ikkala formula ham qabul qilinadi.
        """
        received = str(data.get("sign") or "")
        if not received:
            return False

        invoice_id = data.get("invoice_id", "")
        amount = data.get("amount", "")
        expected_signs = (
            hashlib.sha1(
                f"{data.get('uuid', '')}{invoice_id}{amount}{self.secret}".encode()
            ).hexdigest(),
            hashlib.md5(
                f"{self.store_id}{invoice_id}{amount}{self.secret}".encode()
            ).hexdigest(),
        )
        # compare_digest — timing-attack'dan himoya
        return any(hmac.compare_digest(sign, received) for sign in expected_signs)

    # ---------- Yordamchilar ----------

    @staticmethod
    def to_tiyin(amount) -> int:
        """So'mni tiyinga o'tkazadi.

        Avval 100 ga ko'paytirib keyin butunlanadi — teskari tartibda
        kasr qismi yo'qoladi: int(100.75) * 100 = 10000, to'g'risi 10075.
        """
        return int(Decimal(str(amount)) * 100)

    def _post(self, path: str, payload: dict, headers: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error("Multicard so'rovi muvaffaqiyatsiz: %s — %s", url, exc)
            raise RaxmatError(f"Multicard bilan bog'lanib bo'lmadi: {exc}") from exc
        except ValueError as exc:
            logger.error("Multicard JSON bo'lmagan javob qaytardi: %s", url)
            raise RaxmatError("Multicard kutilmagan javob qaytardi") from exc
