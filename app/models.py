from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, CheckConstraint, func
class Base(DeclarativeBase): pass
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    mobile = Column(String(16), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    invoices = relationship("Invoice", back_populates="customer")
class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(80), nullable=False)
    invoice_date = Column(Date, nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    payment_status = Column(String(20), nullable=False)
    idempotency_key = Column(String(120), nullable=True)
    indexed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    customer = relationship("Customer", back_populates="invoices")
    __table_args__ = (UniqueConstraint("customer_id", "invoice_number", name="uq_invoice_customer_number"), CheckConstraint("amount > 0", name="ck_invoice_amount_positive"))
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(160), nullable=False, default="Customer chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
class OTPChallenge(Base):
    __tablename__ = "otp_challenges"
    id = Column(Integer, primary_key=True)
    mobile = Column(String(16), nullable=False, index=True)
    otp_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    consumed = Column(Boolean, nullable=False, default=False)
    last_sent_at = Column(DateTime(timezone=True), nullable=False)
