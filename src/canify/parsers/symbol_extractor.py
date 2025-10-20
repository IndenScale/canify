"""
符号提取器

负责从项目中提取所有符号，包括实体声明、引用、模式和规范。
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from .entity_declaration_parser import EntityDeclarationParser
from .entity_reference_parser import EntityReferenceParser
from .entity_schema_parser import EntitySchemaParser
from .spec_parser import SpecParser

logger = logging.getLogger(__name__)


class SymbolExtractor:
    """符号提取器"""

    def __init__(self):
        """初始化符号提取器"""
        self.declaration_parser = EntityDeclarationParser()
        self.reference_parser = EntityReferenceParser()
        self.schema_parser = EntitySchemaParser()
        self.spec_parser = SpecParser()

    def extract_from_file(self, file_path: Path) -> Dict[str, Any]:
        """
        从单个文件提取符号

        Args:
            file_path: 文件路径

        Returns:
            符号提取结果
        """
        if not file_path.exists():
            return {
                "file_path": str(file_path),
                "error": "文件不存在"
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            result = {
                "file_path": str(file_path),
                "file_type": self._get_file_type(file_path),
                "symbols": {}
            }

            # 根据文件类型提取不同的符号
            file_type = self._get_file_type(file_path)

            if file_type == "markdown":
                # 提取实体声明和引用
                declarations = self.declaration_parser.parse(content, file_path)
                references = self.reference_parser.parse(content, file_path)

                result["symbols"]["entity_declarations"] = [
                    decl.model_dump() for decl in declarations
                ]
                result["symbols"]["entity_references"] = [
                    ref.model_dump() for ref in references
                ]

            elif file_type == "python":
                # 提取实体模式
                schemas = self.schema_parser.parse(content, file_path)
                result["symbols"]["entity_schemas"] = schemas

            elif file_type == "spec":
                # 提取规范规则
                rules = self.spec_parser.parse(content, file_path)
                result["symbols"]["spec_rules"] = rules

            # 统计信息
            result["statistics"] = self._calculate_statistics(result["symbols"])

            return result

        except Exception as e:
            logger.error(f"提取文件 {file_path} 符号失败: {e}")
            return {
                "file_path": str(file_path),
                "error": str(e)
            }

    def extract_from_directory(self, directory_path: Path) -> Dict[str, Any]:
        """
        从目录提取所有符号

        Args:
            directory_path: 目录路径

        Returns:
            符号提取结果
        """
        if not directory_path.exists():
            return {
                "directory_path": str(directory_path),
                "error": "目录不存在"
            }

        results = {
            "directory_path": str(directory_path),
            "files": [],
            "summary": {}
        }

        # 查找所有相关文件
        files = self._find_relevant_files(directory_path)

        for file_path in files:
            file_result = self.extract_from_file(file_path)
            results["files"].append(file_result)

        # 计算总体统计信息
        results["summary"] = self._calculate_summary(results["files"])

        return results

    def _get_file_type(self, file_path: Path) -> str:
        """
        获取文件类型

        Args:
            file_path: 文件路径

        Returns:
            文件类型
        """
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        if suffix == '.md':
            return "markdown"
        elif suffix == '.py':
            return "python"
        elif suffix in ['.yaml', '.yml'] and name.startswith('spec_'):
            return "spec"
        else:
            return "other"

    def _find_relevant_files(self, directory_path: Path) -> List[Path]:
        """
        查找相关文件

        Args:
            directory_path: 目录路径

        Returns:
            相关文件路径列表
        """
        files = []

        # 查找 Markdown 文件
        files.extend(directory_path.rglob("*.md"))

        # 查找 Python 文件
        files.extend(directory_path.rglob("*.py"))

        # 查找规范文件
        files.extend(directory_path.rglob("spec_*.yaml"))
        files.extend(directory_path.rglob("spec_*.yml"))

        return files

    def _calculate_statistics(self, symbols: Dict[str, Any]) -> Dict[str, int]:
        """
        计算符号统计信息

        Args:
            symbols: 符号字典

        Returns:
            统计信息
        """
        stats = {
            "entity_declarations": 0,
            "entity_references": 0,
            "entity_schemas": 0,
            "spec_rules": 0
        }

        for key in stats.keys():
            if key in symbols:
                stats[key] = len(symbols[key])

        return stats

    def _calculate_summary(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算总体统计信息

        Args:
            files: 文件结果列表

        Returns:
            总体统计信息
        """
        summary = {
            "total_files": len(files),
            "file_types": {},
            "total_symbols": {
                "entity_declarations": 0,
                "entity_references": 0,
                "entity_schemas": 0,
                "spec_rules": 0
            },
            "files_with_errors": 0
        }

        for file_result in files:
            # 统计文件类型
            file_type = file_result.get("file_type", "unknown")
            summary["file_types"][file_type] = summary["file_types"].get(file_type, 0) + 1

            # 统计错误文件
            if "error" in file_result:
                summary["files_with_errors"] += 1

            # 统计符号数量
            if "statistics" in file_result:
                for symbol_type, count in file_result["statistics"].items():
                    if symbol_type in summary["total_symbols"]:
                        summary["total_symbols"][symbol_type] += count

        return summary