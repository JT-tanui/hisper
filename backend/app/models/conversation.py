from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean, JSON, Float
from sqlalchemy.orm import relationship

from ..core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    user_id = Column(String(100), nullable=True)
    summary_text = Column(Text, nullable=True)
    pinned_context = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class AudioBlob(Base):
    __tablename__ = "audio_blobs"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), default="audio/webm")
    duration_ms = Column(Float, nullable=True)
    size_bytes = Column(Integer, default=0)
    provider = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(20), default="user")
    content = Column(Text, default="")
    token_count = Column(Integer, default=0)
    pinned = Column(Boolean, default=False)
    summary = Column(Text, nullable=True)
    audio_blob_id = Column(Integer, ForeignKey("audio_blobs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    audio_blob = relationship("AudioBlob")
