from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime
from enum import Enum

class enum_frameworks(str, Enum):
    pytorch = "PyTorch"
    tensorflow = "TensorFlow"
    lightgbm = "LightGBM"

class ModelCreate(BaseModel):
    name: str
    description: Optional[str] = None

class VersionCreate(BaseModel):
    model_id: UUID
    version_tag: str = Field(..., example="1.0.0")
    framework: enum_frameworks
    promote_to_current: bool = False

class ModelResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    current_version_id: Optional[UUID] = None

class VersionResponse(BaseModel):
    id: UUID
    model_id: UUID
    version_tag: str = Field(..., example="1.0.0")
    framework: enum_frameworks
    current_version: Optional[bool] = False
