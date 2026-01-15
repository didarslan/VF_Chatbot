import uuid
from vfa.core.schemas import SmsResponse

def send_sms(msisdn: str, text: str) -> SmsResponse:
    message_id = str(uuid.uuid4())
    return SmsResponse(message_id=message_id, delivery_status="DELIVERED")

def send_otp(msisdn: str) -> SmsResponse:
    message_id = str(uuid.uuid4())
    return SmsResponse(message_id=message_id, delivery_status="DELIVERED")
