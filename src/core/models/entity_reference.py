"""
实体引用模型

表示在Markdown文档中对实体的引用。
"""

from pydantic import BaseModel, Field

from .location import Location


class EntityReference(BaseModel):
    """
    实体引用模型
    """
    location: Location = Field(..., description="实体引用的位置信息")
    entity_id: str = Field(..., description="被引用的实体ID")
    context_text: str = Field(..., description="引用上下文文本")
    reference_type: str = Field(default="link", description="引用类型")

    def __str__(self) -> str:
        """
        生成引用描述的字符串表示

        Returns:
            引用描述字符串
        """
        return f"引用 {self.entity_id} 在 {self.location}"