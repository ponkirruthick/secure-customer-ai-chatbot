from datetime import date
from decimal import Decimal
from sqlalchemy import select
from app.db import SessionLocal
from app.models import Customer,Invoice
from app.services import invoice_text
from app.vector_store import ensure_collection,upsert_record
DATA=[
("Arun","+919876543210",[("INV-100","2026-09-01","1250","unpaid"),("INV-101","2026-09-04","2200","paid"),("INV-102","2026-09-09","750","unpaid"),("INV-103","2026-09-14","3000","overdue"),("INV-104","2026-09-20","850","paid")]),
("Deepa","+919123456780",[("INV-200","2026-09-02","999","paid"),("INV-201","2026-09-05","1600","unpaid"),("INV-202","2026-09-10","400","unpaid"),("INV-203","2026-09-15","5400","overdue"),("INV-204","2026-09-21","1800","paid")])]
def main():
    db=SessionLocal()
    try:
        try: ensure_collection()
        except Exception: print("Warning: Qdrant/Ollama unavailable; records will still seed into PostgreSQL.")
        for name,mobile,invoices in DATA:
            customer=db.scalar(select(Customer).where(Customer.mobile==mobile))
            if not customer:
                customer=Customer(name=name,mobile=mobile); db.add(customer); db.commit(); db.refresh(customer)
            for number,dt,amount,status in invoices:
                inv=db.scalar(select(Invoice).where(Invoice.customer_id==customer.id,Invoice.invoice_number==number))
                if not inv:
                    inv=Invoice(customer_id=customer.id,invoice_number=number,invoice_date=date.fromisoformat(dt),amount=Decimal(amount),currency="INR",payment_status=status,indexed=False)
                    db.add(inv); db.commit(); db.refresh(inv)
                try: upsert_record(customer.id,"invoice",inv.id,invoice_text(inv)); inv.indexed=True
                except Exception: inv.indexed=False
                db.commit()
        print("Seed finished: Arun and Deepa; five synthetic invoices each.")
    finally: db.close()
if __name__=="__main__": main()
