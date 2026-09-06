"""Pydantic validation models for pipeline configuration.

Provides the `RegressionMetric` enum of supported sklearn scoring metrics and
the `Scoring` / `ModelFeatures` models used to validate the `scoring_type` and
`feature_type` CLI arguments before training.
"""

from enum import Enum
from pydantic import BaseModel
from typing import Literal

class RegressionMetric(str, Enum):
    RMSE = "neg_root_mean_squared_error"
    MAE = "neg_mean_absolute_error"
    R2 = "r2"

class Scoring(BaseModel):
    type: RegressionMetric

class ModelFeatures(BaseModel):
    type: Literal["lag", "rolling"]


