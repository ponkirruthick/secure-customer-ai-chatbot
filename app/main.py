from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.models import Customer, Conversation, Message, Invoice
from app.schemas import OTPRequest, OTPVerify, TokenResponse, ConversationCreate, MessageCreate, InvoiceOut
from app.security import current_customer
from app.services import request_otp, verify_otp, process_chat, invoice_text
from app.vector_store import ensure_collection, upsert_record, search_records
from app.config import settings
app=FastAPI(title="Secure Customer AI Chatbot",version="1.0.0")
@app.on_event("startup")
def startup():
    try:
        ensure_collection()
    except Exception as e:
        print(f"Qdrant startup error: {e}")
@app.get("/health")
def health(): return {"status":"ok","environment":settings.app_env}
@app.post("/auth/request-otp")
def otp_request(body:OTPRequest,db:Session=Depends(get_db)): return request_otp(db,body.mobile)
@app.post("/auth/verify-otp",response_model=TokenResponse)
def otp_verify(body:OTPVerify,db:Session=Depends(get_db)): return verify_otp(db,body.mobile,body.otp)
@app.get("/me")
def me(c:Customer=Depends(current_customer)): return {"id":c.id,"name":c.name,"mobile":c.mobile}
@app.get("/invoices",response_model=list[InvoiceOut])
def invoices(db:Session=Depends(get_db),c:Customer=Depends(current_customer)):
    return db.scalars(select(Invoice).where(Invoice.customer_id==c.id).order_by(Invoice.id)).all()
@app.post("/conversations")
def create_conversation(body:ConversationCreate,db:Session=Depends(get_db),c:Customer=Depends(current_customer)):
    conv=Conversation(customer_id=c.id,title=body.title); db.add(conv); db.commit(); db.refresh(conv)
    return {"id":conv.id,"title":conv.title,"created_at":conv.created_at}
@app.get("/conversations")
def conversations(db:Session=Depends(get_db),c:Customer=Depends(current_customer)):
    rows=db.scalars(select(Conversation).where(Conversation.customer_id==c.id).order_by(Conversation.id.desc())).all()
    return [{"id":x.id,"title":x.title,"created_at":x.created_at} for x in rows]
def owned(db,cid,convid):
    conv=db.scalar(select(Conversation).where(Conversation.id==convid,Conversation.customer_id==cid))
    if not conv: raise HTTPException(404,"Conversation not found")
    return conv
@app.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id:int,db:Session=Depends(get_db),c:Customer=Depends(current_customer)):
    conv=owned(db,c.id,conversation_id); rows=db.scalars(select(Message).where(Message.conversation_id==conv.id).order_by(Message.id)).all()
    return [{"id":m.id,"role":m.role,"content":m.content,"created_at":m.created_at} for m in rows]
@app.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id:int,body:MessageCreate,db:Session=Depends(get_db),c:Customer=Depends(current_customer)):
    conv=owned(db,c.id,conversation_id)
    answer,meta=process_chat(db,c,conv,body.content,body.confirm_invoice,body.pending_invoice)
    return {"conversation_id":conv.id,"answer":answer,"tool_activity":meta}
@app.post("/admin/reindex")
def reindex(db:Session=Depends(get_db),c:Customer=Depends(current_customer)):
    rows=db.scalars(select(Invoice).where(Invoice.customer_id==c.id)).all(); ok=[]; bad=[]
    for inv in rows:
        try: upsert_record(c.id,"invoice",inv.id,invoice_text(inv)); inv.indexed=True; ok.append(inv.id)
        except Exception: inv.indexed=False; bad.append(inv.id)
    db.commit()
    return {"indexed_invoice_ids":ok,"failed_invoice_ids":bad,"message":"PostgreSQL records are preserved even when indexing fails."}
@app.get("/debug/vector-search")
def vector_search(query:str, c:Customer=Depends(current_customer)):
    try: return {"results":search_records(c.id,query)}
    except Exception: raise HTTPException(503,"Vector search unavailable; check Qdrant and Ollama embeddings")
