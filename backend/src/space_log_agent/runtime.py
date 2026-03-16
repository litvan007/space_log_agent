from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from langchain_openai import ChatOpenAI

from space_log_agent.config import AppConfig
from space_log_agent.models import IncidentClassification


class IncidentClassificationClient(Protocol):
    """Protocol of an async classifier returning structured incident output."""

    async def ainvoke(self, input: object, **kwargs: object) -> IncidentClassification:
        """Invoke the classifier with LangChain-compatible input payload."""


@dataclass(frozen=True, slots=True, repr=True)
class IncidentRuntime:
    """Runtime dependencies shared across graph executions."""

    config: AppConfig
    classification_llm: IncidentClassificationClient


def build_incident_runtime(config: AppConfig) -> IncidentRuntime:
    """Build shared runtime dependencies for incident analysis."""

    llm = ChatOpenAI(
        model=config.model_name,
        temperature=0,
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
    ).with_structured_output(IncidentClassification)
    return IncidentRuntime(config=config, classification_llm=llm)
