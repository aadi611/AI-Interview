"""
Unified WebSocket endpoint — handles both text messages and streaming voice audio
in a single connection. There is one interview experience: voice + chat together.
"""
import json
import base64
import traceback
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from datetime import datetime

logger = logging.getLogger(__name__)

from app.core.database import AsyncSessionLocal
from app.core.redis_client import get_redis
from app.models.session import InterviewSession, InterviewStatus
from app.graph.interview_graph import interview_graph
from app.graph.state import InterviewState
from app.services.speech.tts import tts_service
from app.services.speech.stt import stt_service


async def _send_assistant(websocket, text: str):
    """Send an assistant message bundled with its TTS audio so the frontend
    can reveal the text and play the voice together (no drift)."""
    if not text:
        return
    payload = {"type": "message", "content": text, "role": "assistant"}
    try:
        audio_bytes = await tts_service.synthesize(text)
        payload["audio"] = base64.b64encode(audio_bytes).decode()
        payload["format"] = "mp3"
    except Exception as e:
        logger.warning(f"TTS failed: {e}")
    await websocket.send_json(payload)


def _fresh_state(session_id: str, session) -> InterviewState:
    return {
        "session_id": session_id,
        "user_name": "",
        "domain": session.domain,
        "difficulty": session.difficulty,
        "messages": [],
        "onboarding_turns": 0,
        "candidate_background": "",
        "profile_summary": "",
        "current_question_index": 0,
        "questions": [],
        "answers": [],
        "follow_up_count": 0,
        "max_questions": 5,
        "consecutive_correct": 0,
        "consecutive_wrong": 0,
        "evaluation_complete": False,
        "final_score": 0.0,
        "strengths": [],
        "weaknesses": [],
        "improvements": [],
        "overall_feedback": "",
        "stage": "onboarding",
        "should_continue": True,
    }


class InterviewWebSocketHandler:
    async def handle(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        redis = await get_redis()

        audio_buffer: list[bytes] = []
        collecting = False

        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(InterviewSession).where(InterviewSession.id == session_id)
                )
                session = result.scalar_one_or_none()
                if not session:
                    await websocket.send_json({"type": "error", "message": "Session not found"})
                    return

                state_key = f"interview:state:{session_id}"
                init_lock_key = f"interview:init_lock:{session_id}"

                cached = await redis.get(state_key)
                state: InterviewState | None = None
                if cached:
                    state = json.loads(cached)
                    if not state.get("messages"):
                        state = None

                if state:
                    # Reconnect — replay only the last assistant message + audio
                    assistant_msgs = [m for m in state.get("messages", []) if m["role"] == "assistant"]
                    if assistant_msgs:
                        await _send_assistant(websocket, assistant_msgs[-1]["content"])
                else:
                    lock_acquired = await redis.set(init_lock_key, "1", nx=True, ex=30)
                    if not lock_acquired:
                        for _ in range(15):
                            await asyncio.sleep(1)
                            cached = await redis.get(state_key)
                            if cached:
                                break
                        if cached:
                            state = json.loads(cached)
                            assistant_msgs = [m for m in state.get("messages", []) if m["role"] == "assistant"]
                            if assistant_msgs:
                                await _send_assistant(websocket, assistant_msgs[-1]["content"])
                        else:
                            await websocket.send_json({"type": "error", "message": "Session initialization timed out."})
                            return
                    else:
                        try:
                            state = _fresh_state(session_id, session)
                            await websocket.send_json({"type": "typing", "active": True})
                            state = await interview_graph.ainvoke(state)
                            await websocket.send_json({"type": "typing", "active": False})
                            await redis.setex(state_key, 7200, json.dumps(state, default=str))

                            assistant_msgs = [m for m in state.get("messages", []) if m["role"] == "assistant"]
                            if assistant_msgs:
                                await _send_assistant(websocket, assistant_msgs[-1]["content"])

                            session.status = InterviewStatus.IN_PROGRESS
                            session.started_at = datetime.utcnow()
                            await db.commit()
                        finally:
                            await redis.delete(init_lock_key)

                async def process_user_message(user_content: str) -> bool:
                    """Run the graph with a new user message. Returns True if interview finished."""
                    nonlocal state
                    user_content = user_content.strip()
                    if not user_content:
                        return False

                    msgs = list(state.get("messages", []))
                    msgs.append({"role": "user", "content": user_content})
                    state["messages"] = msgs

                    await websocket.send_json({"type": "typing", "active": True})
                    prev_assistant_count = len([m for m in msgs if m["role"] == "assistant"])
                    state = await interview_graph.ainvoke(state)
                    await websocket.send_json({"type": "typing", "active": False})

                    new_assistant_msgs = [
                        m for m in state.get("messages", []) if m["role"] == "assistant"
                    ][prev_assistant_count:]
                    for m in new_assistant_msgs:
                        await _send_assistant(websocket, m["content"])

                    await redis.setex(state_key, 7200, json.dumps(state, default=str))

                    if state.get("stage") == "done":
                        await websocket.send_json({
                            "type": "evaluation",
                            "data": {
                                "score": state.get("final_score"),
                                "strengths": state.get("strengths"),
                                "weaknesses": state.get("weaknesses"),
                                "improvements": state.get("improvements"),
                                "overall_feedback": state.get("overall_feedback"),
                            },
                        })
                        session.status = InterviewStatus.COMPLETED
                        session.completed_at = datetime.utcnow()
                        session.evaluation = {
                            "score": state.get("final_score"),
                            "strengths": state.get("strengths"),
                            "weaknesses": state.get("weaknesses"),
                            "improvements": state.get("improvements"),
                            "overall_feedback": state.get("overall_feedback"),
                            "answers": state.get("answers"),
                        }
                        session.transcript = state.get("messages", [])
                        await db.commit()
                        return True
                    return False

                # Main loop — accept both binary audio frames and text control messages
                while True:
                    try:
                        data = await websocket.receive()
                    except (WebSocketDisconnect, RuntimeError):
                        break

                    if data.get("type") == "websocket.disconnect":
                        break

                    # Audio chunk
                    raw_bytes = data.get("bytes")
                    if raw_bytes is not None:
                        if collecting:
                            audio_buffer.append(raw_bytes)
                        continue

                    raw_text = data.get("text")
                    if raw_text is None:
                        continue

                    try:
                        payload = json.loads(raw_text)
                    except json.JSONDecodeError:
                        continue

                    msg_type = payload.get("type")

                    if msg_type == "start_voice":
                        audio_buffer = []
                        collecting = True

                    elif msg_type == "end_voice":
                        collecting = False
                        if audio_buffer:
                            await websocket.send_json({"type": "processing", "active": True})
                            try:
                                transcript = await stt_service.transcribe_stream(audio_buffer)
                            except Exception as stt_err:
                                logger.error(f"STT error: {stt_err}")
                                transcript = ""
                            audio_buffer = []
                            await websocket.send_json({"type": "processing", "active": False})
                            if transcript and transcript.strip():
                                await websocket.send_json({"type": "transcript", "text": transcript})
                                finished = await process_user_message(transcript)
                                if finished:
                                    break

                    elif msg_type == "interrupt":
                        # User barged in — drop any buffered audio from the prior turn.
                        audio_buffer = []
                        collecting = False

                    elif msg_type == "message":
                        user_content = payload.get("content", "")
                        finished = await process_user_message(user_content)
                        if finished:
                            break

                    elif msg_type == "end":
                        break

        except (WebSocketDisconnect, RuntimeError):
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}\n{traceback.format_exc()}")
            print(f"\n=== WEBSOCKET ERROR ===\n{traceback.format_exc()}\n======================\n")
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass


interview_ws_handler = InterviewWebSocketHandler()
