"""
实体引用模型

表示在Markdown文档中对实体的引用。
"""

from typing import Optional
from pydantic import BaseModel, Field

from .location import Location


class EntityReference(BaseModel):
    """
    实体引用模型
    """
    location: Location = Field(..., description="实体引用的位置信息")
    source_entity_id: Optional[str] = Field(
        None,
        description="源实体ID，对于Markdown文本引用为None"
    )
    target_entity_id: str = Field(
        ...,
        description="被引用的目标实体ID"
    )
    context_text: str = Field(..., description="引用上下文文本")
    reference_type: str = Field(
        default="link",
        description="引用类型: link(文本引用) | field(字段引用)"
    )

    def __str__(self) -> str:
        """
        生成引用描述的字符串表示

        Returns:
            引用描述字符串
        """
        if self.source_entity_id:
            return f"{self.source_entity_id} -> {self.target_entity_id} 在 {self.location}"
        else:
            return f"引用 {self.target_entity_id} 在 {self.location}"
