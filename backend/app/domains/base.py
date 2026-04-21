from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DomainConfig:
    name: str
    display_name: str
    description: str
    topics: list[str]
    evaluation_criteria: list[str]
    system_prompt_addon: str = ""
    sample_questions: list[str] = field(default_factory=list)


class BaseDomain(ABC):
    @property
    @abstractmethod
    def config(self) -> DomainConfig:
        ...
