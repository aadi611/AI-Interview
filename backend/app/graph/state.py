from typing import Literal, TypedDict


# ============================================================
# Shared Types
# ============================================================

Role = Literal["system", "user", "assistant"]
Difficulty = Literal["easy", "medium", "hard"]
InterviewStage = Literal[
    "onboarding",
    "profile",
    "questioning",
    "evaluating",
    "done",
]


# ============================================================
# Conversation
# ============================================================

class Message(TypedDict):
    role: Role
    content: str


# ============================================================
# Candidate
# ============================================================

class CandidateProfile(TypedDict, total=False):
    name: str
    background: str
    summary: str


# ============================================================
# Interview
# ============================================================

class Question(TypedDict):
    id: str
    text: str
    difficulty: Difficulty
    topic: str


class Answer(TypedDict):
    question_id: str
    text: str
    score: float
    feedback: str
    is_correct: bool


# ============================================================
# Evaluation
# ============================================================

class Evaluation(TypedDict, total=False):
    score: float
    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]
    feedback: str


# ============================================================
# Main Interview State
# ============================================================

class InterviewState(TypedDict, total=False):

    # --------------------------------------------------------
    # Session
    # --------------------------------------------------------
    session_id: str

    # --------------------------------------------------------
    # Interview Configuration
    # --------------------------------------------------------
    domain: str
    difficulty: Difficulty
    max_questions: int

    # --------------------------------------------------------
    # Conversation
    # --------------------------------------------------------
    messages: list[Message]

    # --------------------------------------------------------
    # Candidate Profile
    # --------------------------------------------------------
    candidate: CandidateProfile
    onboarding_turns: int

    # --------------------------------------------------------
    # Interview Flow
    # --------------------------------------------------------
    stage: InterviewStage

    # Questions are generated dynamically during the interview.
    questions: list[Question]
    answers: list[Answer]

    # Number of follow-ups for the current question.
    follow_up_count: int

    # --------------------------------------------------------
    # Adaptive Difficulty
    # --------------------------------------------------------
    consecutive_correct: int
    consecutive_wrong: int

    # --------------------------------------------------------
    # Final Evaluation
    # --------------------------------------------------------
    evaluation: Evaluation

    # --------------------------------------------------------
    # Flow Control
    # --------------------------------------------------------
    should_continue: bool