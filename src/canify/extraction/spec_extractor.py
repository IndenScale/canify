"""
Spec 符号提取器

负责从 spec 文件中提取符号信息并构建符号表。
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from ..models.spec import SpecificationRule
from ..parsers.spec_parser import SpecParser
from ..discovery.spec_discoverer import SpecDiscoverer

logger = logging.getLogger(__name__)


class SpecExtractor:
    """Spec 符号提取器"""

    def __init__(self, project_root: Path):
        """
        初始化提取器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.discoverer = SpecDiscoverer(project_root)
        self.parser = SpecParser()

    def extract_all_specs(self) -> List[SpecificationRule]:
        """
        提取项目中的所有 spec 规则

        Returns:
            SpecificationRule 对象列表
        """
        specs = []

        for spec_file in self.discoverer.discover_spec_files_iter():
            file_specs = self.extract_specs_from_file(spec_file)
            specs.extend(file_specs)

        logger.info(f"提取了 {len(specs)} 个 spec 规则")
        return specs

    def extract_specs_from_file(self, file_path: Path) -> List[SpecificationRule]:
        """
        从单个文件中提取 spec 规则

        Args:
            file_path: spec 文件路径

        Returns:
            SpecificationRule 对象列表
        """
        try:
            # 解析文件
            raw_rules = self.parser.parse_file(file_path)

            # 转换为 SpecificationRule 对象
            specs = []
            for raw_rule in raw_rules:
                spec = self._convert_to_specification_rule(raw_rule)
                if spec:
                    specs.append(spec)

            logger.debug(f"从文件 {file_path} 提取了 {len(specs)} 个 spec 规则")
            return specs

        except Exception as e:
            logger.error(f"提取文件 {file_path} 中的 spec 规则失败: {e}")
            return []

    def _convert_to_specification_rule(self, raw_rule: Dict[str, Any]) -> SpecificationRule:
        """
        将原始规则数据转换为 SpecificationRule 对象

        Args:
            raw_rule: 原始规则数据

        Returns:
            SpecificationRule 对象
        """
        try:
            # 构建 SpecificationRule 对象
            spec = SpecificationRule(
                id=raw_rule['id'],
                name=raw_rule['name'],
                description=raw_rule.get('description', ''),
                levels=raw_rule.get('levels', {}),
                fixture=raw_rule.get('fixture', ''),
                test_case=raw_rule.get('test_case', ''),
                env=raw_rule.get('env', 'local'),
                tags=raw_rule.get('tags')
            )
            return spec

        except Exception as e:
            logger.error(f"转换规则 {raw_rule.get('id', 'unknown')} 失败: {e}")
            return None

    def get_spec_by_id(self, spec_id: str) -> SpecificationRule:
        """
        根据 ID 获取 spec 规则

        Args:
            spec_id: 规则 ID

        Returns:
            SpecificationRule 对象，如果未找到则返回 None
        """
        all_specs = self.extract_all_specs()
        for spec in all_specs:
            if spec.id == spec_id:
                return spec
        return None

    def get_specs_by_tag(self, tag: str) -> List[SpecificationRule]:
        """
        根据标签获取 spec 规则

        Args:
            tag: 标签名称

        Returns:
            SpecificationRule 对象列表
        """
        all_specs = self.extract_all_specs()
        return [spec for spec in all_specs if spec.tags and tag in spec.tags]

    def get_all_tags(self) -> List[str]:
        """
        获取所有唯一的标签

        Returns:
            标签列表
        """
        all_specs = self.extract_all_specs()
        tags = set()
        for spec in all_specs:
            if spec.tags:
                tags.update(spec.tags)
        return sorted(list(tags))