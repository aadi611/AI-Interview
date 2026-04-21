import json
import re
from app.graph.state import InterviewState
from app.services.llm.factory import get_llm


GREETING_SYSTEM = """You are a senior {domain} engineer at a top tech company, conducting a live interview.
You are warm, human, and genuinely curious — not a scripted bot.

Open with a short natural greeting (1-2 sentences): introduce yourself by a plausible first name,
mention this is a {difficulty}-level {domain} interview, then ask the candidate to briefly
introduce themselves — their name, years of experience, and what they're currently working on.

Speak like a real person on a video call. No bullet points, no "format explanation",
no lists of what you'll cover. Just a warm opener and ONE open question."""


PROFILE_SYSTEM = """You are a senior {domain} engineer conducting an interview. You have JUST received the
candidate's latest self-introduction or background answer.

Your job: decide whether you need one more clarifying question about their background, OR
whether you have enough context to transition to the first technical question.

Guidelines:
- If the candidate gave a vague intro (just name, one line), ask ONE follow-up about a specific
  project, their tech stack, or a recent challenge they solved. Be genuinely curious — reference
  something specific they said.
- If they gave rich detail (project, stack, years, challenges), transition to the first
  technical question. The question should connect to something they mentioned, not be generic.
- Never ask more than 3 total background questions before starting technical.

Respond with VALID JSON ONLY:
{{
  "action": "probe" | "start_technical",
  "message": "your next spoken line to the candidate — conversational, 1-3 sentences",
  "topic": "sub-topic of the first technical question (only if action=start_technical)",
  "ideal_answer_summary": "brief summary of what a strong answer covers (only if action=start_technical)",
  "expected_keywords": ["kw1", "kw2"]
}}

When you start a technical question, phrase it naturally — e.g. "Since you mentioned working on
X, let me ask you about Y..." — not "Question 1:". Make it {difficulty}-level."""


async def greeting_node(state: InterviewState) -> dict:
    """First invocation only — warm greeting + ask for self-intro."""
    llm = get_llm()
    domain = state["domain"].replace("_", " ")
    difficulty = state["difficulty"]

    system = GREETING_SYSTEM.format(domain=domain, difficulty=difficulty)
    greeting = await llm.chat(
        messages=[{"role": "user", "content": "Open the interview now."}],
        system=system,
    )

    return {
        "stage": "onboarding",
        "onboarding_turns": 0,
        "candidate_background": "",
        "questions": [],
        "answers": [],
        "current_question_index": 0,
        "follow_up_count": 0,
        "max_questions": 5,
        "consecutive_correct": 0,
        "consecutive_wrong": 0,
        "messages": state.get("messages", []) + [{"role": "assistant", "content": greeting.strip()}],
    }


async def profile_node(state: InterviewState) -> dict:
    """After each user onboarding reply — either probe more, or transition to technical."""
    llm = get_llm()
    domain = state["domain"].replace("_", " ")
    difficulty = state["difficulty"]

    messages = state.get("messages", [])
    user_msgs = [m for m in messages if m["role"] == "user"]
    turns = state.get("onboarding_turns", 0) + 1

    # Build conversation context for the LLM
    convo = "\n".join(
        f"{'Interviewer' if m['role']=='assistant' else 'Candidate'}: {m['content']}"
        for m in messages[-8:]
    )

    system = PROFILE_SYSTEM.format(domain=domain, difficulty=difficulty)
    raw = await llm.chat(
        messages=[{
            "role": "user",
            "content": (
                f"Conversation so far:\n{convo}\n\n"
                f"Background questions asked so far: {turns}. Max 3.\n"
                f"Decide your next move and respond in the required JSON format."
            ),
        }],
        system=system,
        max_tokens=800,
    )

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json.loads(match.group()) if match else {"action": "probe", "message": raw.strip()}

    action = parsed.get("action", "probe")
    message = parsed.get("message", "").strip()

    # Accumulate background
    background = state.get("candidate_background", "")
    if user_msgs:
        background = (background + "\n" + user_msgs[-1]["content"]).strip()

    # Force transition after 3 probe turns
    if turns >= 3 and action != "start_technical":
        action = "start_technical"

    result = {
        "onboarding_turns": turns,
        "candidate_background": background,
        "messages": state.get("messages", []) + [{"role": "assistant", "content": message}],
    }

    if action == "start_technical":
        questions = list(state.get("questions", []))
        questions.append({
            "question": message,
            "topic": parsed.get("topic", "general"),
            "difficulty": difficulty,
            "expected_keywords": parsed.get("expected_keywords", []),
            "ideal_answer_summary": parsed.get("ideal_answer_summary", ""),
        })
        result["questions"] = questions
        result["current_question_index"] = 0
        result["stage"] = "questioning"
    else:
        result["stage"] = "onboarding"

    return result
