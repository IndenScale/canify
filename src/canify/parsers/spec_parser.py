"""
规范解析器

负责解析 spec_*.yaml 文件中的业务规则定义。
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


class SpecParser:
    """规范解析器"""

    def parse(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析 YAML 文件中的规范定义

        Args:
            content: 文件内容
            file_path: 文件路径

        Returns:
            规范规则列表
        """
        rules = []

        try:
            # 解析 YAML 内容
            data = yaml.safe_load(content)

            if not data:
                return rules

            # 支持 'specs' 字段（推荐）和 'rules' 字段（向后兼容）
            rules_data = data.get('specs', data.get('rules', []))

            if not rules_data:
                return rules

            for rule_data in rules_data:
                rule = self._parse_rule(rule_data, file_path)
                if rule:
                    rules.append(rule)

        except yaml.YAMLError as e:
            # 如果 YAML 解析失败，返回空列表
            return rules

        return rules

    def _parse_rule(self, rule_data: Dict[str, Any], file_path: Path) -> Optional[Dict[str, Any]]:
        """
        解析单个规则

        Args:
            rule_data: 规则数据
            file_path: 文件路径

        Returns:
            规则信息字典
        """
        if not isinstance(rule_data, dict):
            return None

        # 必需字段检查
        required_fields = ['id', 'name']
        for field in required_fields:
            if field not in rule_data:
                return None

        rule = {
            "id": rule_data['id'],
            "name": rule_data['name'],
            "file_path": str(file_path),
            "type": "business_rule"
        }

        # 可选字段
        optional_fields = [
            'description', 'env', 'levels', 'fixture', 'test_case', 'tags'
        ]

        for field in optional_fields:
            if field in rule_data:
                rule[field] = rule_data[field]

        # 处理 levels 字段
        if 'levels' in rule_data:
            rule['levels'] = rule_data['levels']

        # 提取规则相关的源代码片段
        rule['source_code'] = self._extract_rule_source(rule_data)

        return rule

    def _extract_rule_source(self, rule_data: Dict[str, Any]) -> str:
        """
        提取规则的源代码表示

        Args:
            rule_data: 规则数据

        Returns:
            源代码字符串
        """
        lines = ["rules:"]
        lines.append(f"  - id: {rule_data['id']}")
        lines.append(f"    name: {rule_data['name']}")

        if 'description' in rule_data:
            lines.append(f"    description: {rule_data['description']}")

        if 'env' in rule_data:
            lines.append(f"    env: {rule_data['env']}")

        if 'levels' in rule_data:
            lines.append("    levels:")
            for level, severity in rule_data['levels'].items():
                lines.append(f"      {level}: {severity}")

        if 'fixture' in rule_data:
            lines.append(f"    fixture: {rule_data['fixture']}")

        if 'test_case' in rule_data:
            lines.append(f"    test_case: {rule_data['test_case']}")

        if 'tags' in rule_data:
            lines.append(f"    tags: {rule_data['tags']}")

        return '\n'.join(lines)

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析规范文件

        Args:
            file_path: 文件路径

        Returns:
            规范规则列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse(content, file_path)
        except Exception:
            return []