import json
import re
from app.graph.state import InterviewState
from app.services.llm.factory import get_llm

FEEDBACK_SYSTEM = """You are a senior technical interviewer providing comprehensive feedback.
Be honest, constructive, and specific. Return valid JSON only."""

FEEDBACK_PROMPT = """Generate interview feedback:

Domain: {domain}
Difficulty: {difficulty}
Answers Summary:
{summary}

Return JSON:
{{
  "overall_score": <0-100>,
  "technical_score": <0-100>,
  "communication_score": <0-100>,
  "behavioral_score": <0-100>,
  "hire_recommendation": "strong_yes|yes|maybe|no",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "improvements": ["action 1", "action 2"],
  "overall_feedback": "3-4 paragraph comprehensive feedback"
}}"""


async def feedback_node(state: InterviewState) -> dict:
    llm = get_llm()
    answers = state.get("answers", [])
    questions = state.get("questions", [])

    summary = "\n".join([
        f"Q{i+1} ({questions[a['question_index']]['topic'] if a['question_index'] < len(questions) else 'Unknown'}): "
        f"Score {a.get('score', 0)}/10 | {a.get('brief_feedback', 'N/A')}"
        for i, a in enumerate(answers)
    ]) or "No answers recorded."

    raw = await llm.chat(
        messages=[{"role": "user", "content": FEEDBACK_PROMPT.format(
            domain=state["domain"].replace("_", " ").title(),
            difficulty=state["difficulty"],
            summary=summary,
        )}],
        system=FEEDBACK_SYSTEM,
        max_tokens=2048,
    )

    try:
        feedback = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        feedback = json.loads(match.group()) if match else {}

    closing = await llm.chat(
        messages=[{"role": "user", "content": (
            f"Thank the candidate and give a brief encouraging closing. "
            f"Their score was {feedback.get('overall_score', 'N/A')}/100. 2 sentences max."
        )}],
        system="You are a professional, empathetic interviewer closing an interview session.",
    )

    return {
        "final_score": feedback.get("overall_score", 0),
        "strengths": feedback.get("strengths", []),
        "weaknesses": feedback.get("weaknesses", []),
        "improvements": feedback.get("improvements", []),
        "overall_feedback": feedback.get("overall_feedback", ""),
        "evaluation_complete": True,
        "stage": "done",
        "should_continue": False,
        "messages": state.get("messages", []) + [{"role": "assistant", "content": closing}],
        "_full_evaluation": feedback,
    }
