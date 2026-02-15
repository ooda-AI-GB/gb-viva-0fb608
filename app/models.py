from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False) # who created this ticket (from auth)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False) # enum: "open", "in_progress", "waiting", "resolved", "closed"
    priority = Column(String, nullable=False) # enum: "low", "medium", "high", "urgent"
    category = Column(String, nullable=False) # enum: "bug", "feature_request", "question", "billing", "account", "other"
    assigned_to = Column(String(100), nullable=True)
    customer_email = Column(String, nullable=False)
    customer_name = Column(String(100), nullable=True)
    sla_due = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TicketReply(Base):
    __tablename__ = "ticket_replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    author = Column(String, nullable=False) # who wrote this reply (agent name or "customer")
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False) # markdown supported
    category = Column(String, nullable=False) # enum: "getting_started", "troubleshooting", "billing", "features", "api"
    tags = Column(String, nullable=True) # comma-separated tags
    published = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SLAPolicy(Base):
    __tablename__ = "sla_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    priority = Column(String, nullable=False) # enum matching ticket priority: "low", "medium", "high", "urgent"
    response_hours = Column(Integer, nullable=False)
    resolution_hours = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AIResponse(Base):
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    suggestion_type = Column(String, nullable=False) # enum: "reply_draft", "summary", "categorization"
    content = Column(Text, nullable=False)
    model_used = Column(String, nullable=True)
    accepted = Column(Boolean, default=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
