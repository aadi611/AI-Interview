import json
import base64
import traceback
import logging
from fastapi import WebSocket, WebSocketDisconnect

from app.services.speech.stt import stt_service
from app.services.speech.tts import tts_service

logger = logging.getLogger(__name__)


class VoiceWebSocketHandler:
    async def handle(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        audio_buffer: list[bytes] = []
        collecting = False

        try:
            await self._init_session(websocket, session_id)

            while True:
                try:
                    data = await websocket.receive()
                except (WebSocketDisconnect, RuntimeError):
                    break

                if "bytes" in data:
                    if collecting:
                        audio_buffer.append(data["bytes"])

                elif "text" in data:
                    payload = json.loads(data["text"])
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
                                audio_buffer = []
                                await websocket.send_json({"type": "transcript", "text": transcript})

                                response_text = await self._get_interview_response(session_id, transcript)
                                await websocket.send_json({"type": "processing", "active": False})

                                if response_text:
                                    await websocket.send_json({
                                        "type": "message",
                                        "content": response_text,
                                        "role": "assistant",
                                    })
                                    try:
                                        audio_bytes = await tts_service.synthesize(response_text)
                                        await websocket.send_json({
                                            "type": "audio",
                                            "data": base64.b64encode(audio_bytes).decode(),
                                            "format": "mp3",
                                        })
                                    except Exception as tts_err:
                                        logger.warning(f"TTS failed: {tts_err}")
                            except Exception as e:
                                logger.error(f"Voice processing error: {e}\n{traceback.format_exc()}")
                                await websocket.send_json({"type": "error", "message": str(e)})

                    elif msg_type == "end":
                        break

        except (WebSocketDisconnect, RuntimeError):
            pass
        except Exception as e:
            logger.error(f"Voice WS error: {e}\n{traceback.format_exc()}")
            print(f"\n=== VOICE WS ERROR ===\n{traceback.format_exc()}\n=====================\n")
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass

    async def _init_session(self, websocket: WebSocket, session_id: str):
        """Run onboarding if not cached; send only the last assistant message."""
        from app.core.redis_client import get_redis
        from app.core.database import AsyncSessionLocal
        from app.graph.interview_graph import interview_graph
        from app.models.session import InterviewSession, InterviewStatus
        from sqlalchemy import select
        from datetime import datetime

        redis = await get_redis()
        state_key = f"interview:state:{session_id}"
        init_lock_key = f"interview:init_lock:{session_id}"
        cached = await redis.get(state_key)

        if cached:
            state = json.loads(cached)
            if state.get("messages"):
                # Reconnect: only send the last assistant message
                assistant_msgs = [m for m in state["messages"] if m["role"] == "assistant"]
                if assistant_msgs:
                    await websocket.send_json({
                        "type": "message",
                        "content": assistant_msgs[-1]["content"],
                        "role": "assistant",
                    })
                return

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                await websocket.send_json({"type": "error", "message": "Session not found"})
                return

            lock_acquired = await redis.set(init_lock_key, "1", nx=True, ex=30)
            if not lock_acquired:
                import asyncio
                for _ in range(15):
                    await asyncio.sleep(1)
                    cached = await redis.get(state_key)
                    if cached:
                        break
                if cached:
                    state = json.loads(cached)
                    assistant_msgs = [m for m in state.get("messages", []) if m["role"] == "assistant"]
                    if assistant_msgs:
                        await websocket.send_json({
                            "type": "message",
                            "content": assistant_msgs[-1]["content"],
                            "role": "assistant",
                        })
                return

            try:
                state = {
                    "session_id": session_id,
                    "user_name": "",
                    "domain": session.domain,
                    "difficulty": session.difficulty,
                    "messages": [],
                    "current_question_index": 0,
                    "questions": [],
                    "answers": [],
                    "follow_up_count": 0,
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
                state = await interview_graph.ainvoke(state)
                await redis.setex(state_key, 7200, json.dumps(state, default=str))

                for msg in state.get("messages", []):
                    if msg["role"] == "assistant":
                        await websocket.send_json({"type": "message", "content": msg["content"], "role": "assistant"})

                session.status = InterviewStatus.IN_PROGRESS
                session.started_at = datetime.utcnow()
                await db.commit()
            finally:
                await redis.delete(init_lock_key)

    async def _get_interview_response(self, session_id: str, user_text: str) -> str:
        from app.core.redis_client import get_redis
        from app.graph.interview_graph import interview_graph

        redis = await get_redis()
        state_key = f"interview:state:{session_id}"
        cached = await redis.get(state_key)
        if not cached:
            return "Session expired. Please start a new interview."

        state = json.loads(cached)
        state["messages"] = state.get("messages", []) + [{"role": "user", "content": user_text}]
        state = await interview_graph.ainvoke(state)
        await redis.setex(state_key, 7200, json.dumps(state, default=str))

        assistant_msgs = [m for m in state.get("messages", []) if m["role"] == "assistant"]
        return assistant_msgs[-1]["content"] if assistant_msgs else ""


voice_ws_handler = VoiceWebSocketHandler()
