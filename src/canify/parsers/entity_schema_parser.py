"""
实体模式解析器

负责解析 Python 文件中的实体模式定义。
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class EntitySchemaParser:
    """实体模式解析器"""

    def parse(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析 Python 文件中的实体模式定义

        Args:
            content: 文件内容
            file_path: 文件路径

        Returns:
            实体模式定义列表
        """
        schemas = []

        try:
            # 使用 AST 解析 Python 代码
            tree = ast.parse(content)

            # 查找 Pydantic 模型定义
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    schema = self._extract_schema_from_class(node, file_path)
                    if schema:
                        schemas.append(schema)

        except SyntaxError:
            # 如果 AST 解析失败，使用正则表达式查找
            schemas.extend(self._fallback_parse(content, file_path))

        return schemas

    def _extract_schema_from_class(self, class_node: ast.ClassDef, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        从 AST 类节点提取模式信息

        Args:
            class_node: AST 类节点
            file_path: 文件路径

        Returns:
            模式信息字典
        """
        # 检查是否是 Pydantic 模型
        is_pydantic = False
        for base in class_node.bases:
            if isinstance(base, ast.Name) and 'BaseModel' in base.id:
                is_pydantic = True
                break

        if not is_pydantic:
            return None

        # 提取字段信息
        fields = []
        validators = []

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                field_name = node.target.id
                field_type = ast.unparse(node.annotation) if node.annotation else "Any"

                # 检查是否有默认值
                default_value = None
                if node.value:
                    default_value = ast.unparse(node.value)

                fields.append({
                    "name": field_name,
                    "type": field_type,
                    "default": default_value
                })

            # 提取验证器方法
            elif isinstance(node, ast.FunctionDef):
                validator_info = self._extract_validator_from_function(node)
                if validator_info:
                    validators.append(validator_info)

        # 提取类文档字符串
        docstring = ast.get_docstring(class_node)

        return {
            "name": class_node.name,
            "type": "pydantic_model",
            "file_path": str(file_path),
            "line_number": class_node.lineno,
            "docstring": docstring,
            "fields": fields,
            "validators": validators,
            "source_code": self._extract_class_source(class_node)
        }

    def _extract_validator_from_function(self, func_node: ast.FunctionDef) -> Optional[Dict[str, Any]]:
        """
        从函数定义中提取验证器信息

        Args:
            func_node: AST 函数节点

        Returns:
            验证器信息字典，如果不是验证器则返回 None
        """
        # 检查是否有装饰器
        if not func_node.decorator_list:
            return None

        # 检查是否是 @validator 或 @field_validator 装饰器
        is_validator = False
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                # 检查是否是 validator('field_name') 或 field_validator('field_name')
                if (isinstance(decorator.func, ast.Name) and
                    decorator.func.id in ['validator', 'field_validator']):
                    is_validator = True
                    break
            elif isinstance(decorator, ast.Name):
                # 检查是否是 @validator 或 @field_validator
                if decorator.id in ['validator', 'field_validator']:
                    is_validator = True
                    break

        if not is_validator:
            return None

        # 提取验证器信息
        validator_info = {
            "name": func_node.name,
            "line_number": func_node.lineno,
            "source_code": ast.unparse(func_node) if hasattr(ast, 'unparse') else func_node.name,
            "docstring": ast.get_docstring(func_node)
        }

        # 提取验证的字段名
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                if decorator.func.id in ['validator', 'field_validator'] and decorator.args:
                    if isinstance(decorator.args[0], ast.Constant):
                        validator_info["field_name"] = decorator.args[0].value

        return validator_info

    def _extract_class_source(self, class_node: ast.ClassDef) -> str:
        """
        提取类的源代码

        Args:
            class_node: AST 类节点

        Returns:
            类的源代码字符串
        """
        try:
            return ast.unparse(class_node)
        except:
            # 如果 ast.unparse 不可用，返回简化表示
            return f"class {class_node.name}:"

    def _fallback_parse(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        回退解析方法，使用正则表达式

        Args:
            content: 文件内容
            file_path: 文件路径

        Returns:
            模式定义列表
        """
        schemas = []

        # 查找类定义
        class_pattern = r'class\s+(\w+)\s*\([^)]*BaseModel[^)]*\):'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # 提取类内容
            class_content = self._extract_class_content(content, match.start())

            schemas.append({
                "name": class_name,
                "type": "pydantic_model",
                "file_path": str(file_path),
                "line_number": line_number,
                "fields": [],  # 简化实现
                "source_code": class_content
            })

        return schemas

    def _extract_class_content(self, content: str, start_pos: int) -> str:
        """
        提取类的内容

        Args:
            content: 文件内容
            start_pos: 开始位置

        Returns:
            类的内容字符串
        """
        # 查找类的结束位置
        indent_level = 0
        pos = start_pos

        # 跳过类定义行
        while pos < len(content) and content[pos] != '\n':
            pos += 1
        pos += 1  # 跳过换行符

        # 查找第一个非空行的缩进
        while pos < len(content) and content[pos].isspace():
            if content[pos] == '\n':
                pos += 1
            else:
                indent_level = self._get_indent_level(content, pos)
                break

        # 提取类内容
        class_start = pos
        while pos < len(content):
            if content[pos] == '\n':
                # 检查下一行的缩进
                next_line_start = pos + 1
                if next_line_start >= len(content):
                    break

                next_indent = self._get_indent_level(content, next_line_start)
                if next_indent < indent_level:
                    break
            pos += 1

        return content[class_start:pos].strip()

    def _get_indent_level(self, content: str, pos: int) -> int:
        """
        获取指定位置的缩进级别

        Args:
            content: 文件内容
            pos: 位置

        Returns:
            缩进级别（空格数）
        """
        indent = 0
        while pos < len(content) and content[pos].isspace() and content[pos] != '\n':
            indent += 1
            pos += 1
        return indent