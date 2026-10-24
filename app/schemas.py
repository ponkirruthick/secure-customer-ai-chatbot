from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
class OTPRequest(BaseModel): mobile: str
class OTPVerify(BaseModel):
    mobile: str
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
class ConversationCreate(BaseModel): title: str = Field(default="Customer chat", max_length=160)
class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    confirm_invoice: bool = False
    pending_invoice: dict | None = None
class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    invoice_date: date
    amount: Decimal
    currency: str
    payment_status: str
    indexed: bool
    model_config = ConfigDict(from_attributes=True)
