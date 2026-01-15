from vfa.tools import order_mock, sms_mock

class OrderAgent:
    def create_order_flow(self, msisdn: str, product_url: str, product_name: str, installment_months: int | None) -> dict:
        order = order_mock.create_order(msisdn=msisdn, product_url=product_url, product_name=product_name, installment_months=installment_months)
        sms = sms_mock.send_sms(msisdn, f"Bilgilendirme: Siparişiniz oluşturuldu. OrderID={order.order_id}")
        return {"order": order.model_dump(), "sms": sms.model_dump()}
