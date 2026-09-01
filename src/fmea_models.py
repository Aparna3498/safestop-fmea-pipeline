"""Typed output contract for AI-generated FMEA candidates."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model that rejects fields outside the documented contract."""

    model_config = ConfigDict(extra="forbid")


class Confidence(str, Enum):
    """Permitted confidence labels for candidate screening."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class AIClassification(str, Enum):
    """Permitted AI screening labels; these are not risk ratings."""

    SAFE = "Safe"
    DEGRADED = "Degraded"
    DANGEROUS = "Dangerous"
    DANGEROUS_LATENT = "Dangerous latent"
    UNCERTAIN = "Uncertain"


class FMEACandidate(StrictModel):
    """One preliminary failure-mode candidate requiring human review."""

    candidate_id: str = Field(pattern=r"^AI-\d{3}$")
    element_id: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    local_effect: str = Field(min_length=1)
    system_effect: str = Field(min_length=1)
    hazardous_consequence: str = Field(min_length=1)
    detection_mechanism: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    evidence_references: list[str] = Field(min_length=1)
    confidence: Confidence
    assumptions: list[str]
    missing_information: list[str]
    ai_classification: AIClassification


class FMEAResponse(StrictModel):
    """Wrapper used by the API Structured Outputs parser."""

    candidates: list[FMEACandidate] = Field(min_length=1)
