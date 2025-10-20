"""
实体引用解析器

负责解析 Markdown 文件中的实体引用。
"""

import re
from pathlib import Path
from typing import List

from ..models import EntityReference, Location


class EntityReferenceParser:
    """实体引用解析器"""

    def parse(self, content: str, file_path: Path) -> List[EntityReference]:
        """
        解析文件内容中的实体引用

        Args:
            content: 文件内容
            file_path: 文件路径

        Returns:
            实体引用列表
        """
        references = []
        lines = content.split('\n')

        # 查找 entity:// 格式的引用
        entity_ref_pattern = r'\[([^\]]*)\]\(entity://([^)]+)\)'

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(entity_ref_pattern, line)
            for match in matches:
                reference_text = match.group(1)
                entity_id = match.group(2)

                # 计算列位置
                start_column = match.start() + 1

                location = Location(
                    file_path=file_path,
                    start_line=line_num,
                    end_line=line_num,
                    start_column=start_column
                )

                reference = EntityReference(
                    source_entity_id=None,  # Markdown文本引用没有源实体
                    target_entity_id=entity_id,
                    context_text=reference_text,
                    location=location,
                    reference_type="link"  # 文本引用类型
                )

                references.append(reference)

        return references