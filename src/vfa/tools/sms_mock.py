from __future__ import annotations

import uuid
from vfa.core.schemas import SmsResponse

def send_sms(msisdn: str, text: str) -> SmsResponse:
    _ = text  # mock
    return SmsResponse(message_id=str(uuid.uuid4()), delivery_status="DELIVERED")

def send_otp(msisdn: str) -> SmsResponse:
    _ = msisdn
    return SmsResponse(message_id=str(uuid.uuid4()), delivery_status="DELIVERED")
