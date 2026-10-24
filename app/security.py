from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import Customer
bearer = HTTPBearer(auto_error=False)
def normalize_mobile(mobile: str) -> str:
    digits = "".join(ch for ch in mobile if ch.isdigit())
    if len(digits) == 12 and digits.startswith("91"): digits = digits[2:]
    if len(digits) != 10 or digits[0] not in "6789":
        raise HTTPException(status_code=422, detail="Enter a valid Indian mobile number")
    return "+91" + digits
def make_access_token(customer_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(customer_id), "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes)}, settings.jwt_secret, algorithm="HS256")
def current_customer(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> Customer:
    if not credentials: raise HTTPException(status_code=401, detail="Bearer access token required")
    try:
        data = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        customer_id = int(data["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    customer = db.get(Customer, customer_id)
    if not customer: raise HTTPException(status_code=401, detail="Invalid or expired access token")
    return customer
