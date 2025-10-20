"""
验证引擎

负责协调所有验证器的执行，包括引用验证、Schema验证和业务规则验证。
"""

import logging
from typing import List, Dict, Any

from ..models import View, ValidationResult
from ..storage import SymbolTableManager
from .reference_validator import ReferenceValidator
from .schema_validator import SchemaValidator
from .type_constraint_validator import TypeConstraintValidator

logger = logging.getLogger(__name__)


class ValidationEngine:
    """验证引擎"""

    def __init__(self, symbol_table: SymbolTableManager):
        """
        初始化验证引擎

        Args:
            symbol_table: 符号表管理器
        """
        self.symbol_table = symbol_table
        self.reference_validator = ReferenceValidator(symbol_table)
        self.schema_validator = SchemaValidator(symbol_table)
        self.type_constraint_validator = TypeConstraintValidator(symbol_table)

    def validate_view(self, view: View, project_id: int, verbose: bool = False) -> ValidationResult:
        """
        验证视图

        Args:
            view: 视图对象
            project_id: 项目ID
            verbose: 是否启用详细模式

        Returns:
            验证结果
        """
        logger.info(f"开始验证视图: {view.checkpoint_id}")
        result = ValidationResult.success_result()

        # 1. 引用验证
        reference_result = self._validate_references(view, project_id)
        result.merge(reference_result)

        # 2. Schema验证
        schema_result = self._validate_schemas(view, project_id)
        result.merge(schema_result)

        # 3. Validator执行 (TODO: 实现)
        # validator_result = self._execute_validators(view, project_id)
        # result.merge(validator_result)

        if verbose:
            result.verbose_data = self._collect_verbose_data(project_id)

        logger.info(
            f"验证完成: 成功={result.success}, "
            f"错误={len(result.errors)}, 警告={len(result.warnings)}"
        )

        return result

    def _collect_verbose_data(self, project_id: int) -> Dict[str, Any]:
        """收集详细的诊断数据"""
        symbols = self.symbol_table.get_all_symbols(project_id)
        symbol_data = {
            symbol.entity_id: {
                "type": symbol.entity_type,
                "name": symbol.name,
                "file_path": str(symbol.location.file_path),
                "start_line": symbol.location.start_line,
            }
            for symbol in symbols
        }
        return {"symbol_table": symbol_data}

    def _validate_references(
        self,
        view: View,
        project_id: int
    ) -> ValidationResult:
        """
        验证引用

        Args:
            view: 视图对象
            project_id: 项目ID

        Returns:
            验证结果
        """
        logger.debug("开始引用验证")

        # 获取所有实体
        entities = list(view.entities.values())

        # 执行基础引用验证
        result = self.reference_validator.validate_all(
            project_id, view.references, entities
        )

        # 执行类型约束验证
        type_constraint_result = self.type_constraint_validator.validate_all_references(
            view.references, entities, project_id
        )
        result.merge(type_constraint_result)

        # 检查悬空引用
        dangling_refs = self.reference_validator.get_dangling_references(project_id)
        if dangling_refs:
            logger.warning(f"发现 {len(dangling_refs)} 个悬空引用")
            # 将悬空引用添加为验证错误
            for ref in dangling_refs:
                from ..models import ValidationError, ValidationSeverity
                result.add_error(
                    ValidationError(
                        rule_id="reference-existence",
                        message=f"悬空引用: 实体 '{ref.source_entity_id}' 引用了不存在的实体 '{ref.target_entity_id}'",
                        severity=ValidationSeverity.ERROR,
                        location=ref.location
                    )
                )

        return result

    def _validate_schemas(
        self,
        view: View,
        project_id: int
    ) -> ValidationResult:
        """
        验证Schema

        Args:
            view: 视图对象
            project_id: 项目ID

        Returns:
            验证结果
        """
        logger.debug("开始Schema验证")

        # 获取所有实体
        entities = list(view.entities.values())

        # 执行Schema验证
        result = self.schema_validator.validate_all_entities(entities, project_id)

        return result

    def _execute_validators(
        self,
        view: View,
        project_id: int
    ) -> ValidationResult:
        """
        执行Validator (待实现)

        Args:
            view: 视图对象
            project_id: 项目ID

        Returns:
            验证结果
        """
        # TODO: 实现Validator执行
        # - 执行Schema中的所有@validator装饰的函数
        # - 捕获验证器抛出的异常
        logger.debug("Validator执行 (待实现)")
        return ValidationResult.success_result()