"""Typed shapes the analyzer passes between its steps.

Only data classes live here: field names, types, and light cleanup. No LLM
calls, so other groups can import these and build test objects by hand.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


# What the model writes when a resume does not state something. Treated as "not stated".
_PLACEHOLDERS = {"n/a", "na", "none", "null", "unknown", "not specified", "not stated", "not provided", "not mentioned", "-"}


def _clean(value: str | None) -> str | None:
    """Collapse whitespace; turn an empty string or a placeholder like "N/A" into None."""
    if value is None:
        return None
    value = " ".join(value.split())
    if not value or value.casefold() in _PLACEHOLDERS:
        return None
    return value


def _require_every_field(schema: dict) -> None:
    schema["required"] = list(schema.get("properties", {}))


class Schema(BaseModel):
    """Base class for the analyzer's data classes.

    The JSON schema given to the model lists every field as required. Without
    that, the model skips any field that has a default and whole sections come
    back empty. The Python defaults still apply, so objects built by hand can
    leave fields out.
    """

    model_config = ConfigDict(json_schema_extra=_require_every_field)


class Experience(Schema):
    """One job, internship, or project listed on a resume."""

    title: str = Field(description="Job title or role, as written on the resume")
    organization: str | None = Field(default=None, description="Employer or organization name")
    start: str | None = Field(default=None, description="Start date as written, e.g. 'May 2021'")
    end: str | None = Field(default=None, description="End date as written, or 'Present'")
    description: str | None = Field(default=None, description="Short summary of what the person did in this role")

    @field_validator("title", mode="before")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        return _clean(value) or ""

    @field_validator("organization", "start", "end", "description", mode="before")
    @classmethod
    def _clean_optional(cls, value: str | None) -> str | None:
        return _clean(value)


class Education(Schema):
    """One degree, certificate, or course of study listed on a resume."""

    degree: str = Field(description="Degree or certificate, e.g. 'B.S.' or 'Bachelor of Science'")
    field_of_study: str | None = Field(default=None, description="Field of study or major")
    institution: str | None = Field(default=None, description="School, college, or university name")
    year: str | None = Field(default=None, description="Graduation year or date range as written")

    @field_validator("degree", mode="before")
    @classmethod
    def _clean_degree(cls, value: str) -> str:
        return _clean(value) or ""

    @field_validator("field_of_study", "institution", "year", mode="before")
    @classmethod
    def _clean_optional(cls, value: str | None) -> str | None:
        return _clean(value)


class ResumeProfile(Schema):
    """Structured view of a resume: what the person knows, has done, and has studied."""

    # maxItems is a limit for the model only (it is not enforced on objects built
    # by hand). Without it the model can get stuck repeating list entries until it
    # runs out of tokens, which leaves the JSON cut off and unreadable.
    skills: list[str] = Field(
        default_factory=list,
        description="Skills, tools, and technologies named on the resume, one per item",
        json_schema_extra={"maxItems": 60},
    )
    experience: list[Experience] = Field(
        default_factory=list,
        description="Jobs, internships, and projects",
        json_schema_extra={"maxItems": 12},
    )
    education: list[Education] = Field(
        default_factory=list,
        description="Degrees, certificates, and courses of study",
        json_schema_extra={"maxItems": 8},
    )

    @field_validator("skills", mode="before")
    @classmethod
    def _dedupe_skills(cls, value: list[str] | None) -> list[str]:
        """Trim each skill and drop blanks and repeats (case-insensitive), keeping the first spelling."""
        seen: set[str] = set()
        skills: list[str] = []
        for raw in value or []:
            skill = _clean(raw)
            if skill and skill.casefold() not in seen:
                seen.add(skill.casefold())
                skills.append(skill)
        return skills

    @field_validator("experience", mode="after")
    @classmethod
    def _drop_untitled_experience(cls, value: list[Experience]) -> list[Experience]:
        return [item for item in value if item.title]

    @field_validator("education", mode="after")
    @classmethod
    def _drop_unnamed_education(cls, value: list[Education]) -> list[Education]:
        return [item for item in value if item.degree]

    def missing_sections(self) -> list[str]:
        """Names of the sections that came back empty. An empty list means fully populated."""
        return [name for name in ("skills", "experience", "education") if not getattr(self, name)]

    @property
    def is_fully_populated(self) -> bool:
        return not self.missing_sections()
