"""
引用验证器

负责验证实体引用的正确性，包括存在性检查和类型匹配检查。
"""

import logging
from typing import List, Optional, Dict, Any

from ..models import EntityReference, EntityDeclaration, ValidationResult, ValidationError, ValidationSeverity
from ..storage import SymbolTableManager
from ..types import extract_ref_metadata

logger = logging.getLogger(__name__)


class ReferenceValidator:
    """引用验证器"""

    def __init__(self, symbol_table: SymbolTableManager):
        """
        初始化引用验证器

        Args:
            symbol_table: 符号表管理器
        """
        self.symbol_table = symbol_table

    def validate_all(
        self,
        project_id: int,
        references: List[EntityReference],
        entities: List[EntityDeclaration]
    ) -> ValidationResult:
        """
        验证所有引用

        Args:
            project_id: 项目ID
            references: 引用列表
            entities: 实体列表

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        for reference in references:
            # 基础验证（所有引用）
            basic_result = self._validate_basic(project_id, reference)
            result.merge(basic_result)

            # 类型验证（仅字段引用）
            if reference.source_entity_id is not None:
                type_result = self._validate_type(project_id, reference, entities)
                result.merge(type_result)

            result.total_checks += 1

        return result

    def _validate_basic(
        self,
        project_id: int,
        reference: EntityReference
    ) -> ValidationResult:
        """
        基础验证：验证引用格式和目标实体存在

        Args:
            project_id: 项目ID
            reference: 引用对象

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        # 验证引用格式
        if not reference.target_entity_id:
            error = ValidationError(
                rule_id="reference-format",
                message="引用目标实体ID不能为空",
                severity=ValidationSeverity.ERROR,
                location=reference.location
            )
            result.add_error(error)
            return result

        # 验证目标实体存在
        target_entity = self.symbol_table.get_entity_by_id(
            project_id, reference.target_entity_id
        )

        if target_entity is None:
            error = ValidationError(
                rule_id="reference-existence",
                message=f"引用的实体 '{reference.target_entity_id}' 不存在",
                severity=ValidationSeverity.ERROR,
                location=reference.location,
                entity_id=reference.target_entity_id
            )
            result.add_error(error)

        return result

    def _validate_type(
        self,
        project_id: int,
        reference: EntityReference,
        entities: List[EntityDeclaration]
    ) -> ValidationResult:
        """
        类型验证：验证字段引用的类型匹配

        Args:
            project_id: 项目ID
            reference: 引用对象
            entities: 实体列表

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        # 获取源实体
        source_entity = self.symbol_table.get_entity_by_id(
            project_id, reference.source_entity_id
        )

        if source_entity is None:
            # 源实体不存在，这应该已经被基础验证捕获
            return result

        # 获取目标实体
        target_entity = self.symbol_table.get_entity_by_id(
            project_id, reference.target_entity_id
        )

        if target_entity is None:
            # 目标实体不存在，这应该已经被基础验证捕获
            return result

        # 获取源实体的模式
        source_schema = self.symbol_table.get_schema_by_entity_type(
            project_id, source_entity.entity_type
        )

        if source_schema is None:
            # 源实体没有对应的模式，跳过类型验证
            logger.debug(f"源实体 {source_entity.entity_type} 没有对应的模式，跳过类型验证")
            return result

        # 查找引用对应的字段
        field_info = self._find_reference_field(source_schema, reference)
        if not field_info:
            # 无法确定引用对应的字段，跳过类型验证
            logger.debug(f"无法确定引用对应的字段，跳过类型验证")
            return result

        # 提取字段的类型约束
        field_type_str = field_info["type"]

        # 尝试从字符串中提取类型约束
        target_entity_type = self._extract_type_constraint_from_string(field_type_str)

        if target_entity_type is None:
            # 字段没有类型约束，跳过类型验证
            logger.debug(f"字段 {field_info['name']} 没有类型约束，跳过类型验证")
            return result

        # 调试日志
        logger.debug(f"类型验证: {source_entity.entity_type} -> {target_entity.entity_type}")
        logger.debug(f"字段约束: {field_info['name']} 期望 {target_entity_type}")
        logger.debug(f"实际类型: {target_entity.entity_type}")

        # 验证目标实体类型匹配
        if target_entity.entity_type != target_entity_type:
            error = ValidationError(
                rule_id="reference-type-mismatch",
                message=(
                    f"类型不匹配: 字段 '{field_info['name']}' 期望类型 '{target_entity_type}', "
                    f"但引用的是 '{target_entity.entity_type}' 类型的实体"
                ),
                severity=ValidationSeverity.ERROR,
                location=reference.location,
                entity_id=reference.source_entity_id
            )
            result.add_error(error)

        return result

    def _find_reference_field(
        self,
        schema: Dict[str, Any],
        reference: EntityReference
    ) -> Optional[Dict[str, Any]]:
        """
        查找引用对应的字段

        Args:
            schema: 实体模式
            reference: 引用对象

        Returns:
            字段信息字典，如果找不到则返回None
        """
        # 从引用上下文中提取字段名
        # 这里使用简单的启发式方法：查找包含目标实体ID的字段
        target_id = reference.target_entity_id

        for field in schema.get("fields", []):
            # 检查字段类型是否为引用类型
            field_type = field.get("type", "")
            if "CanifyReference" in field_type or "Ref(" in field_type:
                # 检查引用上下文是否包含字段名
                context = reference.context_text or ""
                field_name = field.get("name", "")

                # 简单的匹配逻辑：如果上下文包含字段名或字段名包含在上下文中
                if field_name in context or context in field_name:
                    return field

                # 或者检查字段默认值是否包含目标实体ID
                default_value = field.get("default", "")
                if target_id in str(default_value):
                    return field

        # 如果找不到精确匹配，返回第一个引用类型的字段
        for field in schema.get("fields", []):
            field_type = field.get("type", "")
            if "CanifyReference" in field_type or "Ref(" in field_type:
                return field

        return None

    def _extract_type_constraint_from_string(self, type_string: str) -> Optional[str]:
        """
        从类型字符串中提取类型约束

        Args:
            type_string: 类型字符串

        Returns:
            目标实体类型，如果没有约束则返回None
        """
        # 查找 Ref('TypeName') 模式
        import re

        # 匹配 Ref('TypeName') 或 Ref("TypeName")
        pattern = r"Ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        match = re.search(pattern, type_string)

        if match:
            return match.group(1)

        # 如果没有找到 Ref 约束，返回 None
        return None

    def get_dangling_references(
        self,
        project_id: int
    ) -> List[EntityReference]:
        """
        获取所有悬空引用

        Args:
            project_id: 项目ID

        Returns:
            悬空引用列表
        """
        return self.symbol_table.get_dangling_references(project_id)