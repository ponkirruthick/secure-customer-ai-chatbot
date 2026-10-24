import secrets, hashlib, json
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.config import settings
from app.models import Customer, Invoice, OTPChallenge, Conversation, Message
from app.security import normalize_mobile, make_access_token
from app.vector_store import upsert_record, search_records
from app.llm import chat
RUNTIME = Path("runtime"); RUNTIME.mkdir(exist_ok=True)
def request_otp(db, raw_mobile):
    mobile = normalize_mobile(raw_mobile); now = datetime.now(timezone.utc)
    latest = db.scalar(select(OTPChallenge).where(OTPChallenge.mobile==mobile).order_by(OTPChallenge.id.desc()))
    if latest and (now-latest.last_sent_at).total_seconds() < settings.otp_resend_seconds:
        raise HTTPException(429, "Please wait before requesting another OTP")
    otp = f"{secrets.randbelow(1000000):06d}"
    c = OTPChallenge(mobile=mobile, otp_hash=hashlib.sha256(otp.encode()).hexdigest(), expires_at=now+timedelta(seconds=settings.otp_ttl_seconds), attempts=0, consumed=False, last_sent_at=now)
    db.add(c); db.commit()
    if settings.app_env.lower()=="development" and settings.dev_otp_delivery:
        (RUNTIME/"dev_otp.txt").write_text(f"Development-only OTP delivery\nMobile: {mobile}\nOTP: {otp}\nExpires: {c.expires_at.isoformat()}\n", encoding="utf-8")
    else:
        raise HTTPException(503, "No SMS delivery adapter configured")
    return {"message":"OTP sent through the configured development delivery channel."}
def verify_otp(db, raw_mobile, otp):
    mobile = normalize_mobile(raw_mobile)
    c = db.scalar(select(OTPChallenge).where(OTPChallenge.mobile==mobile, OTPChallenge.consumed==False).order_by(OTPChallenge.id.desc()))
    now = datetime.now(timezone.utc)
    if not c or c.expires_at <= now: raise HTTPException(401, "Invalid or expired OTP")
    if c.attempts >= settings.otp_max_attempts: raise HTTPException(429, "OTP attempt limit reached")
    c.attempts += 1
    if not secrets.compare_digest(c.otp_hash, hashlib.sha256(otp.encode()).hexdigest()):
        if c.attempts >= settings.otp_max_attempts: c.consumed = True
        db.commit(); raise HTTPException(401, "Invalid or expired OTP")
    c.consumed = True
    customer = db.scalar(select(Customer).where(Customer.mobile==mobile))
    db.commit()
    if not customer: raise HTTPException(401, "This mobile number is not registered")
    return {"access_token":make_access_token(customer.id),"token_type":"bearer","expires_in_seconds":settings.access_token_minutes*60}
def invoice_text(i):
    return f"Invoice ID {i.id}; number={i.invoice_number}; date={i.invoice_date.isoformat()}; amount={i.amount} {i.currency}; status={i.payment_status}"
def save_invoice(db, customer_id, data, idempotency_key=None):
    try:
        number=str(data["invoice_number"]).strip(); inv_date=date.fromisoformat(str(data["invoice_date"]))
        amount=Decimal(str(data["amount"])); currency=str(data.get("currency","INR")).upper(); status=str(data["payment_status"]).lower()
        if not number or amount<=0 or currency not in {"INR","USD","EUR","GBP"} or status not in {"paid","unpaid","overdue"}: raise ValueError()
    except (KeyError, ValueError, InvalidOperation, TypeError):
        raise HTTPException(422,"Invoice needs a valid number, date, positive amount, currency and payment status")
    if idempotency_key and db.scalar(select(Invoice).where(Invoice.customer_id==customer_id,Invoice.idempotency_key==idempotency_key)):
        raise HTTPException(409,"This invoice request was already processed")
    inv=Invoice(customer_id=customer_id,invoice_number=number,invoice_date=inv_date,amount=amount,currency=currency,payment_status=status,idempotency_key=idempotency_key,indexed=False)
    db.add(inv)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"An invoice with this number already exists for this customer")
    db.refresh(inv)
    try:
        upsert_record(customer_id,"invoice",inv.id,invoice_text(inv)); inv.indexed=True
    except Exception:
        inv.indexed=False
    db.commit()
    return inv
TOOLS=[
 {"type":"function","function":{"name":"search_records","description":"Search invoices belonging to the authenticated customer","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
 {"type":"function","function":{"name":"add_invoice","description":"Propose invoice details; do not create before explicit confirmation","parameters":{"type":"object","properties":{"invoice_number":{"type":"string"},"invoice_date":{"type":"string"},"amount":{"type":"number"},"currency":{"type":"string"},"payment_status":{"type":"string"}},"required":["invoice_number","invoice_date","amount","currency","payment_status"]}}}
]
def process_chat(db, customer, conv, text, confirm_invoice=False, pending_invoice=None):
    if confirm_invoice:
        if not pending_invoice: raise HTTPException(422,"Pending invoice details are required")
        inv=save_invoice(db,customer.id,pending_invoice,f"conversation:{conv.id}:{pending_invoice.get('invoice_number')}")
        answer=f"Invoice {inv.invoice_number} saved (ID {inv.id}). "+("It is searchable in Qdrant." if inv.indexed else "It is saved in PostgreSQL but indexing failed; retry with POST /admin/reindex.")
        db.add_all([Message(conversation_id=conv.id,role="user",content=text),Message(conversation_id=conv.id,role="assistant",content=answer)]); db.commit()
        return answer,{"tool":"add_invoice","executed":True,"searchable":inv.indexed}
    history=list(reversed(db.scalars(select(Message).where(Message.conversation_id==conv.id).order_by(Message.id.desc()).limit(settings.history_limit)).all()))
    if text.strip().lower() in {"hi","hello","hey","good morning","good afternoon","good evening"}:
        answer="Hello! How can I help with your customer records or invoices?"
        db.add_all([Message(conversation_id=conv.id,role="user",content=text),Message(conversation_id=conv.id,role="assistant",content=answer)]); db.commit()
        return answer,{"tool":None,"executed":False}
    system={"role":"system","content":"You are a secure customer support assistant. Use tools for invoice facts. Never reveal other customers' data. Cite invoice IDs. add_invoice only proposes details; the application requires separate explicit confirmation."}
    messages=[system]+[{"role":m.role,"content":m.content} for m in history if m.role in ("user","assistant")]+[{"role":"user","content":text}]
    try: response=chat(messages,TOOLS)
    except RuntimeError as e: raise HTTPException(503,str(e))
    calls=response.get("tool_calls") or []; meta={"tool":None,"executed":False}
    if calls:
        fn=calls[0].get("function",{}); name=fn.get("name"); args=fn.get("arguments") or {}
        if isinstance(args,str):
            try: args=json.loads(args)
            except json.JSONDecodeError: args={}
        if name=="search_records":
            try: records=search_records(customer.id,str(args.get("query",text))[:500],5)
            except Exception: records=[]
            if not records:
                rows=db.scalars(select(Invoice).where(Invoice.customer_id==customer.id)).all()
                records=[{"record_id":i.id,"text":invoice_text(i)} for i in rows]
            context="\n".join(r["text"] for r in records[:5]) or "No matching records found."
            final=chat([system,{"role":"user","content":f"Question: {text}\nCustomer-filtered records:\n{context}\nAnswer only from records and cite invoice IDs."}])
            answer=final.get("content","No supported answer available.")
            meta={"tool":"search_records","executed":True,"source_ids":[r.get("record_id") for r in records[:5]]}
        elif name=="add_invoice":
            required={"invoice_number","invoice_date","amount","currency","payment_status"}
            if not required.issubset(args):
                answer="Please provide invoice number, date, positive amount, currency, and payment status."; meta={"tool":"add_invoice","executed":False,"error":"missing_fields"}
            else:
                try:
                    date.fromisoformat(str(args["invoice_date"]))
                    if Decimal(str(args["amount"]))<=0: raise ValueError()
                    proposal={"invoice_number":str(args["invoice_number"]),"invoice_date":str(args["invoice_date"]),"amount":str(args["amount"]),"currency":str(args["currency"]).upper(),"payment_status":str(args["payment_status"]).lower()}
                    answer="Please confirm this invoice before I save it:\n"+json.dumps(proposal,indent=2)+"\nSend a separate confirmation request with these exact details."
                    meta={"tool":"add_invoice","executed":False,"pending_invoice":proposal}
                except Exception:
                    answer="Invoice details are invalid. Please provide a valid date and positive amount."; meta={"tool":"add_invoice","executed":False,"error":"invalid_fields"}
        else:
            answer="Unsupported tool request was rejected."; meta={"tool":name,"executed":False,"error":"unknown_tool"}
    else: answer=response.get("content") or "I could not generate a response."
    db.add_all([Message(conversation_id=conv.id,role="user",content=text),Message(conversation_id=conv.id,role="assistant",content=answer)]); db.commit()
    return answer,meta
