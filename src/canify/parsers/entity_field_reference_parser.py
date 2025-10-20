"""
实体字段引用解析器

负责解析实体声明内部字段中的实体引用。
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from ..models import EntityReference, Location, EntityDeclaration


class EntityFieldReferenceParser:
    """实体字段引用解析器"""

    def parse_from_declaration(
        self,
        declaration: EntityDeclaration,
        file_path: Path
    ) -> List[EntityReference]:
        """
        从实体声明中解析字段引用

        Args:
            declaration: 实体声明对象
            file_path: 文件路径

        Returns:
            实体引用列表
        """
        references = []

        # 递归遍历实体声明的所有字段
        self._extract_references_from_data(
            data=declaration.raw_data,
            source_entity_id=declaration.entity_id,
            file_path=file_path,
            location=declaration.location,
            references=references
        )

        return references

    def _extract_references_from_data(
        self,
        data: Any,
        source_entity_id: str,
        file_path: Path,
        location: Location,
        references: List[EntityReference]
    ) -> None:
        """
        递归提取数据中的实体引用

        Args:
            data: 要检查的数据
            source_entity_id: 源实体ID
            file_path: 文件路径
            location: 位置信息
            references: 引用列表（输出）
        """
        if isinstance(data, str):
            # 检查字符串是否包含 entity:// 引用
            entity_ref_pattern = r'entity://([^\s\)\]\}]+)'
            matches = re.finditer(entity_ref_pattern, data)

            for match in matches:
                entity_id = match.group(1)

                # 创建引用对象
                reference = EntityReference(
                    source_entity_id=source_entity_id,
                    target_entity_id=entity_id,
                    context_text=data,
                    location=location,
                    reference_type="field"  # 字段引用类型
                )
                references.append(reference)

        elif isinstance(data, list):
            # 递归处理列表元素
            for item in data:
                self._extract_references_from_data(
                    item, source_entity_id, file_path, location, references
                )

        elif isinstance(data, dict):
            # 递归处理字典值
            for value in data.values():
                self._extract_references_from_data(
                    value, source_entity_id, file_path, location, references
                )
