import json
import re
from app.graph.state import InterviewState
from app.services.llm.factory import get_llm


NEXT_Q_SYSTEM = """You are a senior {domain} engineer continuing a live interview.

You have the candidate's background and how they answered previous questions. Generate the NEXT
technical question that:
- Builds on what they said they've worked on or know
- Explores a DIFFERENT sub-topic than already covered
- Adapts difficulty: if recent scores were high, go harder; if low, pull back slightly
- Sounds natural, like a human interviewer — reference their earlier answer when useful
  (e.g. "Earlier you mentioned X — let's go deeper into...")

Respond with VALID JSON ONLY:
{{
  "question": "the spoken question, 1-2 sentences, conversational",
  "topic": "sub-topic",
  "difficulty": "easy|medium|hard",
  "expected_keywords": ["kw1", "kw2"],
  "ideal_answer_summary": "brief summary of a strong answer"
}}"""


async def ask_next_question_node(state: InterviewState) -> dict:
    """Generate the next contextual technical question."""
    llm = get_llm()
    domain = state["domain"].replace("_", " ")
    difficulty = state["difficulty"]

    questions = list(state.get("questions", []))
    answers = state.get("answers", [])
    idx = state.get("current_question_index", 0) + 1
    max_q = state.get("max_questions", 5)

    if idx >= max_q:
        return {"stage": "summarizing", "current_question_index": idx}

    covered_topics = [q.get("topic", "") for q in questions]
    recent_scores = [a.get("score", 0) for a in answers[-3:]]
    avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 5

    background = state.get("candidate_background", "")
    history = "\n".join(
        f"Q: {q.get('question','')}\n"
        f"A score: {answers[i].get('score', 'N/A') if i < len(answers) else 'N/A'}/10"
        for i, q in enumerate(questions)
    )

    system = NEXT_Q_SYSTEM.format(domain=domain)
    raw = await llm.chat(
        messages=[{
            "role": "user",
            "content": (
                f"Candidate background:\n{background}\n\n"
                f"Questions asked so far (cover different sub-topics than these): {covered_topics}\n\n"
                f"Recent answer history:\n{history}\n\n"
                f"Recent avg score: {avg_recent:.1f}/10. Baseline difficulty: {difficulty}.\n"
                f"Question number {idx + 1} of {max_q}. Generate the next question."
            ),
        }],
        system=system,
        max_tokens=600,
    )

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json.loads(match.group()) if match else {
            "question": "Can you walk me through a challenging problem you solved recently?",
            "topic": "general",
        }

    questions.append({
        "question": parsed.get("question", ""),
        "topic": parsed.get("topic", "general"),
        "difficulty": parsed.get("difficulty", difficulty),
        "expected_keywords": parsed.get("expected_keywords", []),
        "ideal_answer_summary": parsed.get("ideal_answer_summary", ""),
    })

    return {
        "current_question_index": idx,
        "follow_up_count": 0,
        "stage": "questioning",
        "questions": questions,
        "messages": state.get("messages", []) + [
            {"role": "assistant", "content": parsed.get("question", "")}
        ],
    }
