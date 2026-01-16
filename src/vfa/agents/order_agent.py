from __future__ import annotations

from typing import Any, Dict, Optional
from vfa.tools.order_mock import create_order
from vfa.tools.order_mock import create_order as create_order_tool
from vfa.tools.sms_mock import send_sms


class OrderAgent:
    """
    Order flow runner.
    Manager state'inden (selected_model/url + installment + city + optional msisdn) sipariş üretir.
    """

    def create_order(self, thread_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        ManagerAgent'in çağıracağı fonksiyon.
        Beklenen state alanları:
        - selected_model (str)
        - selected_url (str)
        - installment (int)  -> 12/24/36
        - city (str)         -> teslimat ili (order_mock destekliyorsa)
        - msisdn (str, optional)

        Return:
        {
          "order_id": "...",
          "order": {...},
          "sms": {...} | None
        }
        """
        product_url = state.get("selected_url")
        product_name = state.get("selected_model") or "Bilinmeyen Ürün"
        installment = state.get("installment")
        msisdn = state.get("msisdn")  # opsiyonel

        if not product_url:
            raise ValueError("selected_url boş. Önce cihaz seçimi yapılmalı.")

        installment_months: Optional[int] = int(installment) if installment else None

        # msisdn yoksa mock için güvenli placeholder (SMS atmayı da opsiyonel tutuyoruz)
        msisdn_safe = msisdn or "05000000000"

        order = create_order_tool(msisdn_safe, product_url, product_name, installment_months)

        sms_payload = None
        # Placeholder numaraya SMS atmayalım (istersen bunu kaldırıp her zaman gönderebilirsin)
        if msisdn:
            sms = send_sms(msisdn, f"Bilgilendirme: Sipariş oluşturuldu. OrderID={order.order_id}")
            sms_payload = sms.model_dump()

        return {
            "order_id": order.order_id,
            "order": order.model_dump(),
            "sms": sms_payload,
        }

    # Geriye dönük uyumluluk (eski çağrı şekli)
    def create_order_flow(
        self,
        msisdn: str,
        product_url: str,
        product_name: str,
        installment_months: Optional[int],
    ) -> Dict[str, Any]:
        order = create_order(msisdn, product_url, product_name, installment_months)
        sms = send_sms(msisdn, f"Bilgilendirme: Sipariş oluşturuldu. OrderID={order.order_id}")
        return {"order": order.model_dump(), "sms": sms.model_dump()}
