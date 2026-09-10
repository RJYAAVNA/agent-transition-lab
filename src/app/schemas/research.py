from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ResearchRequest(BaseModel):
    topic: ShortText


class Signal(BaseModel):
    title: ShortText
    description: LongText


class Opportunity(BaseModel):
    title: ShortText
    description: LongText


class Risk(BaseModel):
    title: ShortText
    description: LongText


class Evidence(BaseModel):
    title: ShortText
    source: ShortText
    url: HttpUrl | None = None
    excerpt: LongText | None = None


class ResearchResponse(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    topic: ShortText
    summary: LongText
    signals: list[Signal] = Field(min_length=1)
    opportunities: list[Opportunity] = Field(min_length=1)
    risks: list[Risk] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
