"""
Canify 约束 (Specification) 模型
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SpecificationRule(BaseModel):
    """
    表示从 spec_*.yaml 文件中解析出的单条业务规则。
    """
    id: str = Field(..., description="规则的唯一标识符")
    name: str = Field(..., description="规则的可读名称")
    description: str = Field("", description="规则的详细描述")
    levels: Dict[str, str] = Field(..., description="规则在不同验证模式下的严重级别, 例如: {'verify': 'warning', 'validate': 'error'}")
    fixture: str = Field(..., description="为规则提供数据的 fixture 函数的引用路径, 例如: 'my_fixtures.project_tasks_pairs'")
    test_case: str = Field(..., description="执行验证逻辑的测试用例函数的引用路径, 例如: 'my_tests.check_budget'")
    env: str = Field("local", description="规则执行环境: local 或 remote")
    tags: Optional[List[str]] = Field(None, description="规则的标签列表，用于过滤")

    class Config:
        frozen = True
