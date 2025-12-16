from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.conversation import Conversation, Message, AudioBlob

logger = logging.getLogger(__name__)


class ConversationService:
    """Manage conversation history and summarization."""

    def __init__(self, token_budget: int = 800):
        self.token_budget = token_budget

    async def get_or_create_conversation(
        self, db: AsyncSession, conversation_id: Optional[int] = None, user_id: Optional[str] = None
    ) -> Conversation:
        if conversation_id:
            result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation

        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    async def add_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        role: str,
        content: str,
        audio_blob: Optional[AudioBlob] = None,
        pinned: bool = False,
    ) -> Message:
        token_count = self._estimate_tokens(content)
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_count=token_count,
            pinned=pinned,
            audio_blob=audio_blob,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    async def attach_audio(
        self,
        db: AsyncSession,
        conversation_id: int,
        file_path: str,
        mime_type: str,
        size_bytes: int,
        duration_ms: Optional[float] = None,
        provider: Optional[str] = None,
    ) -> AudioBlob:
        audio_blob = AudioBlob(
            file_path=file_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            duration_ms=duration_ms,
            provider=provider,
        )
        db.add(audio_blob)
        await db.commit()
        await db.refresh(audio_blob)
        return audio_blob

    async def slice_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        max_tokens: Optional[int] = None,
        include_summaries: bool = True,
    ) -> List[Message]:
        budget = max_tokens or self.token_budget
        result = await db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
        messages: List[Message] = list(result.scalars().all())

        pinned = [m for m in messages if m.pinned]
        unpinned = [m for m in messages if not m.pinned]

        included: List[Message] = []
        used_tokens = sum(m.token_count for m in pinned)
        included.extend(pinned)

        for message in reversed(unpinned):
            if used_tokens + message.token_count > budget:
                continue
            included.insert(len(pinned), message)
            used_tokens += message.token_count

        if include_summaries:
            conversation_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conversation = conversation_result.scalar_one_or_none()
            if conversation and conversation.summary_text:
                summary_message = Message(
                    id=-1,
                    conversation_id=conversation_id,
                    role="summary",
                    content=conversation.summary_text,
                    token_count=self._estimate_tokens(conversation.summary_text),
                    pinned=True,
                    created_at=datetime.utcnow(),
                )
                included.insert(0, summary_message)
        return included

    async def update_summary(self, db: AsyncSession, conversation_id: int, keep_last: int = 5) -> None:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = list(result.scalars().all())
        if len(messages) <= keep_last:
            return

        historical = messages[:-keep_last]
        summary = "\n".join([f"{m.role}: {m.content[:200]}" for m in historical])

        convo_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conversation = convo_result.scalar_one_or_none()
        if conversation:
            conversation.summary_text = summary
            conversation.updated_at = datetime.utcnow()
            await db.commit()

    def _estimate_tokens(self, content: str) -> int:
        return max(1, len(content.split()))


conversation_service = ConversationService()
