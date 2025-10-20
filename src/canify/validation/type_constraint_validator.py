"""
类型约束验证器

负责验证实体引用是否符合类型约束。
"""

import logging
from typing import Dict, Any, List, Optional

from ..models import EntityDeclaration, EntityReference, ValidationResult
from ..storage import SymbolTableManager

logger = logging.getLogger(__name__)


class TypeConstraintValidator:
    """类型约束验证器"""

    def __init__(self, symbol_table: SymbolTableManager):
        """
        初始化类型约束验证器

        Args:
            symbol_table: 符号表管理器
        """
        self.symbol_table = symbol_table

    def validate_reference(self, reference: EntityReference, target_entity: EntityDeclaration, project_id: int) -> ValidationResult:
        """
        验证单个引用是否符合类型约束

        Args:
            reference: 实体引用
            target_entity: 目标实体
            project_id: 项目ID

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        # 获取源实体的类型（如果有）
        source_entity_type = self._get_source_entity_type(reference, project_id)
        if not source_entity_type:
            # 没有源实体类型信息，跳过类型约束验证
            return result

        # 获取目标实体类型
        target_entity_type = target_entity.entity_type

        # 检查类型兼容性
        if not self._is_type_compatible(source_entity_type, target_entity_type):
            from ..models import ValidationError as CanifyValidationError, ValidationSeverity
            result.add_error(
                CanifyValidationError(
                    rule_id="type-constraint-mismatch",
                    message=f"类型不匹配: 源实体类型 '{source_entity_type}' 不能引用目标实体类型 '{target_entity_type}'",
                    severity=ValidationSeverity.ERROR,
                    location=reference.location
                )
            )
            logger.warning(
                f"类型约束验证失败: {reference.source_entity_id or '文本'} -> {target_entity.entity_id} "
                f"({source_entity_type} -> {target_entity_type})"
            )

        return result

    def validate_all_references(self, references: List[EntityReference], entities: List[EntityDeclaration], project_id: int) -> ValidationResult:
        """
        验证所有引用是否符合类型约束

        Args:
            references: 实体引用列表
            entities: 实体声明列表
            project_id: 项目ID

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        # 构建实体查找字典
        entity_dict = {entity.entity_id: entity for entity in entities}

        for reference in references:
            # 查找目标实体
            target_entity = entity_dict.get(reference.target_entity_id)
            if not target_entity:
                # 目标实体不存在，由引用验证器处理
                continue

            # 验证类型约束
            reference_result = self.validate_reference(reference, target_entity, project_id)
            result.merge(reference_result)

        logger.info(
            f"类型约束验证完成: 成功={result.success}, "
            f"错误={len(result.errors)}, 警告={len(result.warnings)}"
        )

        return result

    def _get_source_entity_type(self, reference: EntityReference, project_id: int) -> Optional[str]:
        """
        获取源实体的类型

        Args:
            reference: 实体引用
            project_id: 项目ID

        Returns:
            源实体类型，如果无法获取则返回 None
        """
        if not reference.source_entity_id:
            # 文本引用，没有源实体类型
            return None

        try:
            # 从符号表中获取源实体
            source_entity = self.symbol_table.get_entity_by_id(project_id, reference.source_entity_id)
            if source_entity:
                return source_entity.entity_type
        except Exception as e:
            logger.warning(f"获取源实体类型失败: {e}")

        return None

    def _is_type_compatible(self, source_type: str, target_type: str) -> bool:
        """
        检查源类型和目标类型是否兼容

        Args:
            source_type: 源实体类型
            target_type: 目标实体类型

        Returns:
            类型是否兼容
        """
        # 基础类型兼容性规则
        # 1. 相同类型总是兼容
        if source_type == target_type:
            return True

        # 2. 类型继承关系检查（需要扩展支持类型继承）
        # 目前实现基本的类型兼容性检查
        # 可以扩展为基于类型系统的复杂检查

        # 3. 默认情况下，不同类型不兼容
        # 未来可以支持类型别名、类型继承等高级特性

        return False

    def add_type_compatibility_rule(self, source_type: str, target_type: str):
        """
        添加类型兼容性规则（预留接口）

        Args:
            source_type: 源类型
            target_type: 目标类型
        """
        # 预留接口，用于支持自定义类型兼容性规则
        # 例如：source_type 可以引用 target_type
        logger.debug(f"添加类型兼容性规则: {source_type} -> {target_type}")

    def add_type_inheritance(self, child_type: str, parent_type: str):
        """
        添加类型继承关系（预留接口）

        Args:
            child_type: 子类型
            parent_type: 父类型
        """
        # 预留接口，用于支持类型继承系统
        # 例如：child_type 继承自 parent_type
        logger.debug(f"添加类型继承关系: {child_type} 继承自 {parent_type}")