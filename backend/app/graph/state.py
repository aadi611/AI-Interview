from typing import TypedDict


class InterviewState(TypedDict, total=False):
    # Identity
    session_id: str
    user_name: str
    domain: str
    difficulty: str

    # Conversation — plain dicts {role, content}, no LangChain reducer
    messages: list[dict]

    # Candidate profile (filled during onboarding)
    onboarding_turns: int
    candidate_background: str
    profile_summary: str  # distilled bullet points about experience

    # Interview progress — dynamic questions now, not pre-generated
    current_question_index: int
    questions: list[dict]  # accumulated as the interview progresses
    answers: list[dict]
    follow_up_count: int
    max_questions: int

    # Adaptive difficulty
    consecutive_correct: int
    consecutive_wrong: int

    # Evaluation
    evaluation_complete: bool
    final_score: float
    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]
    overall_feedback: str

    # Flow control — stage drives routing
    # onboarding | profile | questioning | evaluating | done
    stage: str
    should_continue: bool
