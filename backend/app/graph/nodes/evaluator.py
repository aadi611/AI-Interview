import json
import re
from app.graph.state import InterviewState
from app.services.llm.factory import get_llm

EVAL_SYSTEM = """You are an expert technical interviewer evaluating a candidate's answer.
Be objective and constructive. Return valid JSON only — no markdown."""

EVAL_PROMPT = """Evaluate this interview answer.

Question: {question}
Topic: {topic}
Difficulty: {difficulty}
Expected Keywords: {keywords}
Ideal Answer Summary: {ideal}

Candidate's Answer: {answer}

Return JSON:
{{
  "score": <0-10 float>,
  "technical_correctness": <0-10>,
  "communication_clarity": <0-10>,
  "completeness": <0-10>,
  "strengths": ["..."],
  "gaps": ["..."],
  "brief_feedback": "2-3 sentence feedback for internal notes",
  "needs_followup": <true if the answer is shallow or has a specific gap worth probing>
}}"""

FOLLOWUP_SYSTEM = """You are a senior engineer probing deeper on a specific gap. Like a real interviewer,
briefly acknowledge what the candidate said (1 short phrase), then ask ONE specific follow-up that
drills into the gap. Conversational, human. No preamble like "great answer" — be natural.
2 sentences max."""


async def evaluator_node(state: InterviewState) -> dict:
    """Score the latest answer, decide whether to follow up, ask next, or finish."""
    llm = get_llm()
    messages = state.get("messages", [])
    questions = state.get("questions", [])
    idx = state.get("current_question_index", 0)
    max_q = state.get("max_questions", 5)

    user_msgs = [m for m in messages if m["role"] == "user"]
    if not user_msgs:
        return {"stage": "questioning"}

    answer = user_msgs[-1]["content"]
    q_data = questions[idx] if idx < len(questions) else {}

    raw = await llm.chat(
        messages=[{"role": "user", "content": EVAL_PROMPT.format(
            question=q_data.get("question", ""),
            topic=q_data.get("topic", ""),
            difficulty=q_data.get("difficulty", state["difficulty"]),
            keywords=q_data.get("expected_keywords", []),
            ideal=q_data.get("ideal_answer_summary", ""),
            answer=answer,
        )}],
        system=EVAL_SYSTEM,
        max_tokens=800,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group()) if match else {"score": 5, "needs_followup": False}

    answers = list(state.get("answers", []))
    answers.append({"question_index": idx, "answer": answer, **result})

    score = result.get("score", 5)
    cc = state.get("consecutive_correct", 0)
    cw = state.get("consecutive_wrong", 0)
    if score >= 7:
        cc += 1; cw = 0
    elif score < 5:
        cw += 1; cc = 0
    else:
        cc = 0; cw = 0

    needs_followup = result.get("needs_followup", False) and state.get("follow_up_count", 0) < 2

    # Decide next stage
    next_idx = idx + 1
    if needs_followup:
        next_stage = "follow_up"
    elif next_idx >= max_q:
        next_stage = "summarizing"
    else:
        next_stage = "next_question"

    return {
        "answers": answers,
        "consecutive_correct": cc,
        "consecutive_wrong": cw,
        "stage": next_stage,
    }


async def follow_up_node(state: InterviewState) -> dict:
    """Deep-dive probe — briefly acknowledge, then ask one targeted question."""
    llm = get_llm()
    questions = state.get("questions", [])
    idx = state.get("current_question_index", 0)
    answers = state.get("answers", [])

    q_data = questions[idx] if idx < len(questions) else {}
    last_answer = answers[-1] if answers else {}
    gaps = last_answer.get("gaps", [])

    follow_up = await llm.chat(
        messages=[{"role": "user", "content": (
            f"Original question: {q_data.get('question', '')}\n"
            f"Candidate's answer (summary): {last_answer.get('answer', '')[:500]}\n"
            f"Specific gaps to probe: {', '.join(gaps) if gaps else 'missing depth'}\n\n"
            "Acknowledge briefly and ask ONE targeted follow-up."
        )}],
        system=FOLLOWUP_SYSTEM,
        max_tokens=200,
    )

    return {
        "follow_up_count": state.get("follow_up_count", 0) + 1,
        "stage": "questioning",
        "messages": state.get("messages", []) + [{"role": "assistant", "content": follow_up.strip()}],
    }
