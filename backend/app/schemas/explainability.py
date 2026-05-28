from typing import Literal

from pydantic import BaseModel, Field


class ExplanationFeature(BaseModel):
    name: str
    importance: float
    display_value: str | None = None


class ModelExplanation(BaseModel):
    model: Literal["TFT", "TabNet"]
    prediction_label: str | None = None
    churn_probability: float | None = None
    top_features: list[ExplanationFeature]
    explanation_type: str
    notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CustomerExplanationResponse(BaseModel):
    customer_id: str
    models: list[ModelExplanation]
    warnings: list[str] = Field(default_factory=list)
    source: str
    artifact_version: dict[str, str] | None = None
