from app.domains.base import DomainConfig

# All domain configs registered here — add new domains by appending to this dict

DSA = DomainConfig(
    name="dsa",
    display_name="Data Structures & Algorithms",
    description="Arrays, trees, graphs, dynamic programming, sorting, searching",
    topics=["arrays", "linked lists", "trees", "graphs", "dynamic programming",
            "sorting", "searching", "hashing", "recursion", "complexity analysis"],
    evaluation_criteria=["correctness", "time complexity", "space complexity",
                         "edge cases", "code quality", "problem-solving approach"],
    sample_questions=[
        "Explain the difference between BFS and DFS. When would you use each?",
        "What is dynamic programming? Give an example problem.",
        "How would you detect a cycle in a directed graph?",
    ],
)

SYSTEM_DESIGN = DomainConfig(
    name="system_design",
    display_name="System Design",
    description="Scalable system architecture, distributed systems, databases",
    topics=["scalability", "load balancing", "caching", "databases", "microservices",
            "message queues", "CDN", "consistency", "availability", "API design"],
    evaluation_criteria=["clarity of thought", "scalability awareness", "trade-off analysis",
                         "component knowledge", "estimation skills", "real-world experience"],
    sample_questions=[
        "Design a URL shortener like bit.ly.",
        "How would you design Twitter's feed system?",
        "Explain CAP theorem with a real-world example.",
    ],
)

HR = DomainConfig(
    name="hr",
    display_name="HR Interview",
    description="Cultural fit, motivation, goals, and workplace scenarios",
    topics=["motivation", "career goals", "teamwork", "conflict resolution",
            "leadership", "work ethic", "company culture", "salary expectations"],
    evaluation_criteria=["communication", "self-awareness", "professionalism",
                         "cultural fit", "growth mindset", "honesty"],
    sample_questions=[
        "Tell me about yourself.",
        "Where do you see yourself in 5 years?",
        "Why do you want to leave your current role?",
    ],
)

BEHAVIORAL = DomainConfig(
    name="behavioral",
    display_name="Behavioral Interview",
    description="STAR-method scenarios, past experience, soft skills",
    topics=["leadership", "conflict", "teamwork", "failure", "success",
            "initiative", "adaptability", "communication", "problem-solving"],
    evaluation_criteria=["STAR structure", "specificity", "impact", "reflection",
                         "communication clarity", "self-awareness"],
    sample_questions=[
        "Tell me about a time you failed. What did you learn?",
        "Describe a situation where you had a conflict with a teammate.",
        "Give an example of a time you showed leadership.",
    ],
)

FRONTEND = DomainConfig(
    name="frontend",
    display_name="Frontend Engineering",
    description="React, browser APIs, CSS, performance, accessibility",
    topics=["React", "JavaScript", "TypeScript", "CSS", "performance",
            "accessibility", "browser APIs", "state management", "testing"],
    evaluation_criteria=["technical depth", "browser knowledge", "performance awareness",
                         "accessibility", "modern practices", "code quality"],
    sample_questions=[
        "Explain the virtual DOM and why React uses it.",
        "What is the difference between useMemo and useCallback?",
        "How do you optimize a slow React application?",
    ],
)

BACKEND = DomainConfig(
    name="backend",
    display_name="Backend Engineering",
    description="APIs, databases, caching, authentication, microservices",
    topics=["REST", "GraphQL", "databases", "caching", "authentication",
            "authorization", "microservices", "message queues", "testing", "security"],
    evaluation_criteria=["API design", "database knowledge", "security awareness",
                         "scalability", "testing practices", "reliability"],
    sample_questions=[
        "What are the differences between SQL and NoSQL databases?",
        "How would you implement JWT authentication?",
        "Explain database indexing and when to use it.",
    ],
)

ML = DomainConfig(
    name="ml",
    display_name="Machine Learning",
    description="ML algorithms, model training, evaluation, deployment",
    topics=["supervised learning", "unsupervised learning", "neural networks",
            "evaluation metrics", "feature engineering", "overfitting", "MLOps"],
    evaluation_criteria=["algorithmic knowledge", "mathematical understanding",
                         "practical experience", "evaluation skills", "deployment awareness"],
    sample_questions=[
        "Explain the bias-variance tradeoff.",
        "How do you handle class imbalance?",
        "What is the difference between L1 and L2 regularization?",
    ],
)

DOMAIN_REGISTRY: dict[str, DomainConfig] = {
    "dsa": DSA,
    "system_design": SYSTEM_DESIGN,
    "hr": HR,
    "behavioral": BEHAVIORAL,
    "frontend": FRONTEND,
    "backend": BACKEND,
    "ml": ML,
}


def get_domain(name: str) -> DomainConfig:
    domain = DOMAIN_REGISTRY.get(name.lower())
    if not domain:
        raise ValueError(f"Unknown domain: {name}. Available: {list(DOMAIN_REGISTRY.keys())}")
    return domain


def list_domains() -> list[dict]:
    return [
        {
            "name": d.name,
            "display_name": d.display_name,
            "description": d.description,
            "topics": d.topics,
        }
        for d in DOMAIN_REGISTRY.values()
    ]
