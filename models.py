"""Tables: users, complaints, status_history.

Status is not overwritten in place. Each change is a new history row,
so you can answer "who changed this ticket, and when?"
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(40), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    complaints = relationship("Complaint", back_populates="owner")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(10), nullable=False, default="medium")
    status = Column(String(20), nullable=False, default="open")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    owner = relationship("User", back_populates="complaints")
    history = relationship("StatusHistory", back_populates="complaint", order_by="StatusHistory.id")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(String(200), default="")
    changed_at = Column(DateTime, default=utcnow, nullable=False)
    complaint = relationship("Complaint", back_populates="history")
