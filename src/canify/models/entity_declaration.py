"""
实体声明模型

表示在Markdown文档中定义的实体。
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

from .location import Location


class EntityDeclaration(BaseModel):
    """
    实体声明模型
    """
    location: Location = Field(..., description="实体声明的位置信息")
    entity_type: str = Field(..., description="实体类型")
    entity_id: str = Field(..., description="实体唯一标识符")
    name: str = Field(..., description="实体显示名称")
    raw_data: Dict[str, Any] = Field(..., description="原始实体数据")
    source_code: str = Field(..., description="原始代码块内容")

    def __str__(self) -> str:
        """
        生成实体描述的字符串表示

        Returns:
            实体描述字符串
        """
        return f"{self.entity_type}::{self.entity_id} ({self.name})"
