"""
实体声明解析器

解析Markdown文件中的实体定义代码块。
"""

import re
import yaml
from pathlib import Path
from typing import List

from ..models import EntityDeclaration, Location


class EntityDeclarationParser:
    """
    实体声明解析器

    负责解析Markdown文件中的 ````entity` 代码块。
    """

    # 匹配实体声明代码块的正则表达式
    ENTITY_BLOCK_PATTERN = re.compile(
        r'```entity\s*\n(.*?)\n```',
        re.DOTALL | re.MULTILINE
    )

    def parse(self, content: str, file_path: Path) -> List[EntityDeclaration]:
        """
        解析Markdown内容中的实体声明

        Args:
            content: Markdown文件内容
            file_path: 文件路径

        Returns:
            实体声明列表
        """
        declarations = []

        # 查找所有实体声明代码块
        for match in self.ENTITY_BLOCK_PATTERN.finditer(content):
            try:
                entity_data = self._parse_entity_block(match, content, file_path)
                if entity_data:
                    declarations.append(entity_data)
            except Exception as e:
                # 记录解析错误，但继续处理其他实体
                print(f"解析实体声明时出错: {e}")
                continue

        return declarations

    def _parse_entity_block(self, match: re.Match, content: str, file_path: Path) -> EntityDeclaration:
        """
        解析单个实体声明代码块

        Args:
            match: 正则匹配结果
            content: 完整文件内容
            file_path: 文件路径

        Returns:
            实体声明对象

        Raises:
            ValueError: 当实体数据格式无效时
        """
        block_content = match.group(1).strip()

        # 解析YAML内容
        try:
            raw_data = yaml.safe_load(block_content)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {e}")

        if not isinstance(raw_data, dict):
            raise ValueError("实体声明必须是YAML字典格式")

        # 验证必需字段
        required_fields = ["type", "id", "name"]
        for field in required_fields:
            if field not in raw_data:
                raise ValueError(f"实体声明缺少必需字段: {field}")

        # 计算位置信息
        location = self._calculate_location(match, content, file_path)

        return EntityDeclaration(
            location=location,
            entity_type=raw_data["type"],
            entity_id=raw_data["id"],
            name=raw_data["name"],
            raw_data=raw_data,
            source_code=block_content
        )

    def _calculate_location(self, match: re.Match, content: str, file_path: Path) -> Location:
        """
        计算代码块的位置信息

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