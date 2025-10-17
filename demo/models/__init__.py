"""
Canify 实体模型配置

这是用户定义的实体模型配置文件，Canify 会动态加载这些模型来进行验证。
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class CanifyEntity(BaseModel):
    """基础实体模型"""
    type: str = Field(..., description="实体类型")
    id: str = Field(..., description="实体唯一标识符")
    name: str = Field(..., description="实体显示名称")


class Project(CanifyEntity):
    """项目实体"""
    type: str = "project"
    budget: Optional[float] = None
    status: str = "draft"
    manager: Optional[str] = None
    developers: List[str] = []


class Task(CanifyEntity):
    """任务实体"""
    type: str = "task"
    project_id: str
    assignee: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    status: str = "pending"
    dependencies: List[str] = []


class User(CanifyEntity):
    """用户实体"""
    type: str = "user"
    email: Optional[str] = None
    role: Optional[str] = None
    skills: List[str] = []