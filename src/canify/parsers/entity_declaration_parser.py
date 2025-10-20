"""
实体声明解析器

负责解析 Markdown 文件中的实体声明。
"""

import re
import yaml
from pathlib import Path
from typing import List, Optional, Optional

from ..models import EntityDeclaration, Location


class EntityDeclarationParser:
    """实体声明解析器"""

    def parse(self, content: str, file_path: Path) -> List[EntityDeclaration]:
        """
        从 Markdown 文件尾部的 ```entity 代码块中解析实体声明。
        """
        declarations = []
        # Regex to find all ```entity blocks
        pattern = r"```entity\s*\n(.*?)\n```"

        for match in re.finditer(pattern, content, re.DOTALL):
            yaml_content = match.group(1)
            source_code = match.group(0)

            # Calculate line number
            start_line = content[:match.start()].count('\n') + 1
            end_line = content[:match.end()].count('\n') + 1

            try:
                declaration = self._parse_yaml_to_declaration(
                    yaml_content, source_code, file_path, start_line, end_line
                )
                if declaration:
                    declarations.append(declaration)
            except yaml.YAMLError:
                # In case of malformed YAML, just skip this block.
                # A linter could report this as an error.
                continue

        return declarations

    def _parse_yaml_to_declaration(
        self,
        yaml_content: str,
        source_code: str,
        file_path: Path,
        start_line: int,
        end_line: int
    ) -> Optional[EntityDeclaration]:
        """
        将解析后的 YAML 内容转换为 EntityDeclaration 对象。
        """
        raw_data = yaml.safe_load(yaml_content)

        if not isinstance(raw_data, dict):
            return None

        # 检查必需字段
        if 'id' not in raw_data or 'type' not in raw_data or 'name' not in raw_data:
            return None

        # 创建实体声明
        location = Location(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_column=1,
            end_column=1 # Simplified
        )

        return EntityDeclaration(
            location=location,
            entity_type=raw_data['type'],
            entity_id=raw_data['id'],
            name=raw_data['name'],
            raw_data=raw_data,
            source_code=source_code
        )