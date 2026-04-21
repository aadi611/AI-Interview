import re
from langgraph.graph import StateGraph, END
from app.graph.state import InterviewState
from app.graph.nodes.onboarding import greeting_node, profile_node
from app.graph.nodes.question_gen import ask_next_question_node
from app.graph.nodes.evaluator import evaluator_node, follow_up_node
from app.graph.nodes.feedback import feedback_node


# Phrases that signal the candidate wants to wrap up the interview.
_END_INTENT_RE = re.compile(
    r"\b("
    r"end (the|this) interview"
    r"|stop (the|this) interview"
    r"|you can end (the|this) interview"
    r"|let'?s (end|stop|wrap up|conclude)"
    r"|i(?:'| a)?m done( now)?"
    r"|i (would|'?d) (like|want) to (end|stop|wrap up|finish)"
    r"|(please )?(end|finish|wrap up|conclude) (the )?interview"
    r"|that'?s (all|enough)( for (me|today))?"
    r"|no more questions"
    r")\b",
    re.IGNORECASE,
)


def _wants_to_end(text: str) -> bool:
    if not text:
        return False
    return bool(_END_INTENT_RE.search(text))


def route_entry(state: InterviewState) -> str:
    """Decide where to enter the graph based on current state."""
    messages = state.get("messages", [])
    stage = state.get("stage", "")

    # First invocation — nothing has been said yet
    if not messages:
        return "greeting"

    # Need a user message to process
    last = messages[-1]
    if last.get("role") != "user":
        return END

    # Candidate explicitly asked to end the interview — jump straight to wrap-up.
    if _wants_to_end(last.get("content", "")):
        return "generate_feedback"

    # Onboarding phase: user just answered a background question
    if stage in ("onboarding", "", "profile"):
        return "profile"

    # Questioning phase: user just answered a technical question
    if stage in ("questioning",):
        return "evaluate_answer"

    return END


def route_after_profile(state: InterviewState) -> str:
    """After profile: either wait for user reply or (if transitioned) wait for answer."""
    # Either way, we've already sent a message — wait for user input
    return END


def route_after_evaluation(state: InterviewState) -> str:
    stage = state.get("stage", "")
    if stage == "follow_up":
        return "follow_up"
    if stage == "summarizing":
        return "generate_feedback"
    return "ask_next_question"


def route_after_ask_next(state: InterviewState) -> str:
    if state.get("stage") == "summarizing":
        return "generate_feedback"
    return END


def build_interview_graph():
    graph = StateGraph(InterviewState)

    graph.add_node("greeting", greeting_node)
    graph.add_node("profile", profile_node)
    graph.add_node("ask_next_question", ask_next_question_node)
    graph.add_node("evaluate_answer", evaluator_node)
    graph.add_node("follow_up", follow_up_node)
    graph.add_node("generate_feedback", feedback_node)

    graph.set_conditional_entry_point(
        route_entry,
        {
            "greeting": "greeting",
            "profile": "profile",
            "evaluate_answer": "evaluate_answer",
            "generate_feedback": "generate_feedback",
            END: END,
        },
    )

    graph.add_edge("greeting", END)
    graph.add_conditional_edges("profile", route_after_profile, {END: END})
    graph.add_conditional_edges(
        "evaluate_answer",
        route_after_evaluation,
        {
            "follow_up": "follow_up",
            "ask_next_question": "ask_next_question",
            "generate_feedback": "generate_feedback",
        },
    )
    graph.add_edge("follow_up", END)
    graph.add_conditional_edges(
        "ask_next_question",
        route_after_ask_next,
        {"generate_feedback": "generate_feedback", END: END},
    )
    graph.add_edge("generate_feedback", END)

    return graph.compile()


interview_graph = build_interview_graph()
