"""
实体引用解析器

解析Markdown文件中的实体引用链接。
"""

import re
from pathlib import Path
from typing import List

from ..models import EntityReference, Location


class EntityReferenceParser:
    """
    实体引用解析器

    负责解析Markdown文件中的 `[文本](entity://<ID>)` 引用链接。
    """

    # 匹配实体引用链接的正则表达式
    ENTITY_REFERENCE_PATTERN = re.compile(
        r'\[(.*?)\]\(entity://([^\s)]+)\)',
        re.MULTILINE
    )

    def parse(self, content: str, file_path: Path) -> List[EntityReference]:
        """
        解析Markdown内容中的实体引用

        Args:
            content: Markdown文件内容
            file_path: 文件路径

        Returns:
            实体引用列表
        """
        references = []

        # 查找所有实体引用链接
        for match in self.ENTITY_REFERENCE_PATTERN.finditer(content):
            try:
                reference = self._parse_reference(match, content, file_path)
                if reference:
                    references.append(reference)
            except Exception as e:
                # 记录解析错误，但继续处理其他引用
                print(f"解析实体引用时出错: {e}")
                continue

        return references

    def _parse_reference(self, match: re.Match, content: str, file_path: Path) -> EntityReference:
        """
        解析单个实体引用

        Args:
            match: 正则匹配结果
            content: 完整文件内容
            file_path: 文件路径

        Returns:
            实体引用对象
        """
        context_text = match.group(1).strip()
        entity_id = match.group(2).strip()

        # 计算位置信息
        location = self._calculate_location(match, content, file_path)

        return EntityReference(
            location=location,
            entity_id=entity_id,
            context_text=context_text,
            reference_type="link"
        )

    def _calculate_location(self, match: re.Match, content: str, file_path: Path) -> Location:
        """
        计算引用链接的位置信息

        Args:
            match: 正则匹配结果
            content: 完整文件内容
            file_path: 文件路径

        Returns:
            位置信息对象
        """
        start_pos = match.start()
        end_pos = match.end()

        # 计算起始行号
        start_line = content[:start_pos].count('\n') + 1

        # 计算结束行号
        end_line = content[:end_pos].count('\n') + 1

        return Location(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line
        )