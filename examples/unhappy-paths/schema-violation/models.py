"""
Schema定义
"""

from pydantic import BaseModel, field_validator
from typing import Annotated
from src.canify.types import CanifyReference, Ref


class User(BaseModel):
    id: str
    type: str
    name: str
    role: str

    @field_validator("role")
    def role_must_be_valid(cls, v):
        valid_roles = ["Engineer", "Manager", "Designer"]
        if v not in valid_roles:
            raise ValueError(f"角色必须是以下之一: {valid_roles}")
        return v


class Project(BaseModel):
    id: str
    type: str
    name: str
    owner: Annotated[CanifyReference, Ref("User")]
    budget: int

    @field_validator("budget")
    def budget_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("预算必须是正数")
        return v