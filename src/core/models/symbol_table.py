"""
符号表模型

存储所有实体声明和引用的全局符号信息。
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .entity_declaration import EntityDeclaration
from .entity_reference import EntityReference


class SymbolTable(BaseModel):
    """
    符号表模型
    """
    entities: dict[str, EntityDeclaration] = Field(
        default_factory=dict,
        description="实体ID到实体声明的映射"
    )
    references: list[EntityReference] = Field(
        default_factory=list,
        description="所有实体引用列表"
    )
    entity_types: dict[str, list[EntityDeclaration]] = Field(
        default_factory=dict,
        description="实体类型到实体列表的映射"
    )

    def add_entity(self, entity: EntityDeclaration) -> None:
        """
        添加实体到符号表

        Args:
            entity: 要添加的实体声明
        """
        self.entities[entity.entity_id] = entity

        # 按类型分组
        if entity.entity_type not in self.entity_types:
            self.entity_types[entity.entity_type] = []
        self.entity_types[entity.entity_type].append(entity)

    def add_reference(self, reference: EntityReference) -> None:
        """
        添加引用到符号表

        Args:
            reference: 要添加的实体引用
        """
        self.references.append(reference)

    def find_entity(self, entity_id: str) -> Optional[EntityDeclaration]:
        """
        根据实体ID查找实体

        Args:
            entity_id: 要查找的实体ID

        Returns:
            找到的实体声明，如果不存在则返回None
        """
        return self.entities.get(entity_id)

    def get_references_to(self, entity_id: str) -> List[EntityReference]:
        """
        获取指向特定实体的所有引用

        Args:
            entity_id: 目标实体ID

        Returns:
            指向该实体的引用列表
        """
        return [ref for ref in self.references if ref.entity_id == entity_id]

    def get_entities_by_type(self, entity_type: str) -> List[EntityDeclaration]:
        """
        获取特定类型的所有实体

        Args:
            entity_type: 实体类型

        Returns:
            该类型的所有实体列表
        """
        return self.entity_types.get(entity_type, [])

    @property
    def total_entities(self) -> int:
        """
        获取实体总数

        Returns:
            实体总数
        """
        return len(self.entities)

    @property
    def total_references(self) -> int:
        """
        获取引用总数

        Returns:
            引用总数
        """
        return len(self.references)