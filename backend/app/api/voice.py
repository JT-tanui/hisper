import json
import os
import tempfile
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import verify_api_key
from ..services.conversation_service import conversation_service
from ..models.conversation import Message

router = APIRouter(dependencies=[Depends(verify_api_key)])

AUDIO_STORAGE = os.path.join(os.path.dirname(__file__), "..", "..", "audio_blobs")
MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10MB

os.makedirs(os.path.abspath(AUDIO_STORAGE), exist_ok=True)


def _ensure_size(file: UploadFile):
    content_length = 0
    try:
        if file.size:
            content_length = file.size
    except AttributeError:
        pass
    if content_length and content_length > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio too large")


def _format_message_payload(message: Message):
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "audio_blob_id": message.audio_blob_id,
        "pinned": message.pinned,
    }


@router.post("/start")
async def start_voice(
    conversation_id: Optional[int] = Form(None),
    user_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    conversation = await conversation_service.get_or_create_conversation(db, conversation_id, user_id)
    return {"conversation_id": conversation.id, "pinned_context": conversation.pinned_context or []}


@router.post("/stream")
async def stream_voice(
    conversation_id: int = Form(...),
    role: str = Form("user"),
    provider: str = Form("openai"),
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    _ensure_size(audio)
    conversation = await conversation_service.get_or_create_conversation(db, conversation_id)

    suffix = os.path.splitext(audio.filename or "audio.webm")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=os.path.abspath(AUDIO_STORAGE)) as temp_file:
        content = await audio.read()
        if len(content) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Audio too large")
        temp_file.write(content)
        temp_file.flush()
        file_path = temp_file.name

    audio_blob = await conversation_service.attach_audio(
        db,
        conversation_id=conversation.id,
        file_path=file_path,
        mime_type=audio.content_type or "audio/webm",
        size_bytes=len(content),
        provider=provider,
    )

    transcript_snippet = f"Received {len(content)} bytes via {provider}"
    message = await conversation_service.add_message(
        db,
        conversation_id=conversation.id,
        role=role,
        content=transcript_snippet,
        audio_blob=audio_blob,
    )

    async def event_stream() -> AsyncGenerator[bytes, None]:
        chunk = json.dumps({"transcript_chunk": transcript_snippet, "message": _format_message_payload(message)})
        yield chunk.encode()

    return StreamingResponse(event_stream(), media_type="application/json")


@router.post("/stop")
async def stop_voice(
    conversation_id: int = Form(...),
    transcript: Optional[str] = Form(None),
    provider: str = Form("openai"),
    db: AsyncSession = Depends(get_db),
):
    conversation = await conversation_service.get_or_create_conversation(db, conversation_id)
    final_transcript = transcript or "Voice session ended"
    message = await conversation_service.add_message(
        db,
        conversation_id=conversation.id,
        role="assistant",
        content=final_transcript,
    )
    await conversation_service.update_summary(db, conversation.id)
    return {"message": _format_message_payload(message), "provider": provider}
