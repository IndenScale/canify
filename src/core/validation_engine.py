"""
Canify 验证引擎

实现多阶段验证：符号发现、引用关联、数据模型校验、业务规则校验。
"""
import importlib
import sys
import os
import yaml
from typing import List, Dict, Any
from pathlib import Path

from .models import EntityDeclaration, EntityReference, SymbolTable, Location, ValidationResult, ValidationError
from .exceptions import (
    DuplicateEntityIdError,
    DanglingReferenceError,
    CircularDependencyError,
    MissingRequiredFieldError,
    InvalidFieldValueError,
    TypeValidationError,
    BusinessRuleViolation,
    CanifyValidationError,
)


class ValidationEngine:
    """
    验证引擎

    负责执行多阶段验证。
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.validation_errors: List[Exception] = []
        self.validation_warnings: List[Exception] = []
        self.project_root: Path = Path(".")
        self.mode = "verify"
        self.strict = False

    def validate(self, declarations: List[EntityDeclaration], references: List[EntityReference], project_root: Path, mode: str, strict: bool = False) -> ValidationResult:
        """
        执行完整的验证流程

        Args:
            declarations: 实体声明列表
            references: 实体引用列表
            project_root: 被验证的项目根目录
            mode: 验证模式 (e.g., 'lint', 'verify')
            strict: 是否启用严格模式 (将警告视为错误)

        Returns:
            一个包含验证结果的 ValidationResult 对象
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        self.project_root = project_root
        self.mode = mode
        self.strict = strict

        # 内置规则：这些规则的严重性是硬编码的，未来可以重构为内部 spec
        try:
            self._symbol_discovery(declarations)
            self._reference_validation(references)
            self._schema_validation(declarations)
        except CanifyValidationError as e:
            # 内置规则目前总是作为错误处理
            self.validation_errors.append(e)

        # 用户自定义规则：基于 spec 文件
        try:
            self._business_rule_validation()
        except CanifyValidationError as e:
            self.validation_errors.append(e)

        # 将 Python 异常对象转换为 ValidationError 对象
        validation_errors = [self._convert_exception_to_validation_error(e) for e in self.validation_errors]
        validation_warnings = [self._convert_exception_to_validation_error(e) for e in self.validation_warnings]

        return ValidationResult(
            success=len(self.validation_errors) == 0,
            errors=validation_errors,
            warnings=validation_warnings
        )

    def _business_rule_validation(self):
        """
        阶段四：执行基于 spec 的业务规则校验
        """
        constraints_path = self.project_root / "constraints"
        if not constraints_path.is_dir():
            return

        if str(constraints_path) not in sys.path:
            sys.path.insert(0, str(constraints_path))

        try:
            spec_files = self._find_spec_files(constraints_path)
            for spec_file in spec_files:
                self._load_and_run_rules(spec_file)
        finally:
            if str(constraints_path) in sys.path:
                sys.path.remove(str(constraints_path))

    def _find_spec_files(self, constraints_path: Path) -> List[Path]:
        return list(constraints_path.glob("spec_*.yaml"))

    def _load_and_run_rules(self, spec_file: Path):
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec_data = yaml.safe_load(f)
        except Exception as e:
            self.validation_errors.append(CanifyValidationError(f"无法解析 spec 文件 {spec_file.name}: {e}"))
            return

        if not spec_data or "rules" not in spec_data:
            return

        for rule in spec_data.get("rules", []) :
            try:
                module_path, func_name = rule["test_case"].rsplit('.', 1)
                module = importlib.import_module(module_path)
                test_case_func = getattr(module, func_name)

                scope = rule.get("scope", "cross-entity")
                if scope == "cross-entity":
                    test_case_func(self.symbol_table)
                elif scope == "intra-entity":
                    target_type = rule.get("target_entity")
                    if not target_type:
                        raise CanifyValidationError(f"规则 '{rule['id']}' 的 scope 是 intra-entity，但缺少 target_entity 字段")

                    for entity in self.symbol_table.get_entities_by_type(target_type):
                        test_case_func(entity)

            except BusinessRuleViolation as e:
                level_for_mode = rule.get("levels", {}).get(self.mode)
                if level_for_mode == "error":
                    self.validation_errors.append(e)
                elif level_for_mode == "warning":
                    if self.strict:
                        self.validation_errors.append(BusinessRuleViolation(e.rule_id, f"[提升为错误] {e.message}", e.location))
                    else:
                        self.validation_warnings.append(e)
            except Exception as e:
                self.validation_errors.append(
                    CanifyValidationError(f"执行规则 '{rule.get('id', 'N/A')}' 时出错: {e}")
                )


    def _symbol_discovery(self, declarations: List[EntityDeclaration]) -> None:
        """
        符号发现阶段

        验证实体声明的符号正确性，包括：
        - 重复的实体ID
        - 必需字段检查
        """
        # 检查重复的实体ID
        entity_ids: Dict[str, List[Location]] = {}

        for declaration in declarations:
            entity_id = declaration.entity_id
            if entity_id in entity_ids:
                entity_ids[entity_id].append(declaration.location)
            else:
                entity_ids[entity_id] = [declaration.location]

        # 报告重复的实体ID
        for entity_id, locations in entity_ids.items():
            if len(locations) > 1:
                raise DuplicateEntityIdError(entity_id, locations)

        # 检查必需字段
        for declaration in declarations:
            self._validate_required_fields(declaration)

        # 构建符号表（即使有错误也要构建，以便后续验证）
        for declaration in declarations:
            self.symbol_table.add_entity(declaration)

    def _validate_required_fields(self, declaration: EntityDeclaration) -> None:
        """
        验证实体声明的必需字段

        Args:
            declaration: 实体声明

        Raises:
            MissingRequiredFieldError: 当缺少必需字段时
        """
        required_fields = ["type", "id", "name"]

        for field in required_fields:
            if field not in declaration.raw_data:
                raise MissingRequiredFieldError(field, declaration.location)

    def _reference_validation(self, references: List[EntityReference]) -> None:
        """
        引用关联阶段

        验证实体引用的正确性，包括：
        - 悬空引用检查
        - 循环依赖检测
        """
        # 检查悬空引用
        for reference in references:
            entity = self.symbol_table.find_entity(reference.entity_id)
            if not entity:
                raise DanglingReferenceError(reference.entity_id, reference.location)

        # 检查循环依赖（简化的实现）
        self._check_circular_dependencies()

    def _check_circular_dependencies(self) -> None:
        """
        检查循环依赖

        这是一个简化的实现，实际项目中可能需要更复杂的图算法。
        """
        # TODO: 实现更复杂的循环依赖检测
        # 目前只检查自引用
        for reference in self.symbol_table.references:
            entity = self.symbol_table.find_entity(reference.entity_id)
            if entity and entity.entity_id == reference.entity_id:
                # 自引用可能在某些场景下是合法的
                # 这里只是示例，实际项目中需要根据业务规则判断
                pass

    def _schema_validation(self, declarations: List[EntityDeclaration]) -> None:
        """
        数据模型校验阶段

        验证实体数据的类型和格式正确性。
        """
        for declaration in declarations:
            self._validate_entity_schema(declaration)

    def _validate_entity_schema(self, declaration: EntityDeclaration) -> None:
        """
        验证单个实体的数据模型

        Args:
            declaration: 实体声明

        Raises:
            TypeValidationError: 当字段类型不匹配时
            InvalidFieldValueError: 当字段值无效时
        """
        raw_data = declaration.raw_data

        # 验证字段类型
        if "budget" in raw_data:
            budget_value = raw_data["budget"]
            # 检查是否为占位符
            if self._is_placeholder(budget_value):
                if self.mode == "validate":  # Strict 模式禁止占位符
                    raise TypeValidationError(
                        "budget",
                        str(budget_value),
                        "数字",
                        declaration.location
                    )
                # Lax 模式下允许占位符，跳过类型检查
            elif not isinstance(budget_value, (int, float)):
                raise TypeValidationError(
                    "budget",
                    str(budget_value),
                    "数字",
                    declaration.location
                )

        if "status" in raw_data:
            status_value = raw_data["status"]
            # 检查是否为占位符
            if self._is_placeholder(status_value):
                valid_statuses = ["active", "inactive", "completed", "cancelled", "in-progress"]
                if self.mode == "validate":  # Strict 模式禁止占位符
                    raise InvalidFieldValueError(
                        "status",
                        status_value,
                        f"有效值: {', '.join(valid_statuses)}",
                        declaration.location
                    )
                # Lax 模式下允许占位符，跳过状态检查
            else:
                valid_statuses = ["active", "inactive", "completed", "cancelled", "in-progress"]
                if status_value not in valid_statuses:
                    raise InvalidFieldValueError(
                        "status",
                        status_value,
                        f"有效值: {', '.join(valid_statuses)}",
                        declaration.location
                    )

        if "developers" in raw_data:
            developers_value = raw_data["developers"]
            if not isinstance(developers_value, list):
                raise TypeValidationError(
                    "developers",
                    str(developers_value),
                    "列表",
                    declaration.location
                )

    def get_errors(self) -> List[Exception]:
        """
        获取验证过程中收集的所有错误

        Returns:
            错误列表
        """
        return self.validation_errors

    def get_symbol_table(self) -> SymbolTable:
        """
        获取构建的符号表

        Returns:
            符号表对象
        """
        return self.symbol_table

    def _is_placeholder(self, value: Any) -> bool:
        """
        检查值是否为占位符

        Args:
            value: 要检查的值

        Returns:
            如果是占位符返回 True，否则返回 False
        """
        if not isinstance(value, str):
            return False

        placeholders = ["TBD", "TODO", "待定", "待完成", "?"]
        return value.strip().upper() in [p.upper() for p in placeholders]

    def _convert_exception_to_validation_error(self, exception: Exception) -> ValidationError:
        """
        将 Python 异常对象转换为 ValidationError 对象

        Args:
            exception: Python 异常对象

        Returns:
            ValidationError 对象
        """
        if isinstance(exception, ValidationError):
            return exception

        # 处理各种 Canify 异常类型
        if isinstance(exception, DuplicateEntityIdError):
            return ValidationError(
                severity="error",
                message=str(exception),
                location=exception.location,
                entity_id=exception.entity_id,
                error_type="duplicate_entity_id"
            )
        elif isinstance(exception, DanglingReferenceError):
            return ValidationError(
                severity="error",
                message=str(exception),
                location=exception.location,
                entity_id=exception.entity_id,
                error_type="dangling_reference"
            )
        elif isinstance(exception, MissingRequiredFieldError):
            return ValidationError(
                severity="error",
                message=str(exception),
                location=exception.location,
                error_type="missing_required_field"
            )
        elif isinstance(exception, TypeValidationError):
            return ValidationError(
                severity="error",
                message=str(exception),
                location=exception.location,
                error_type="type_validation"
            )
        elif isinstance(exception, InvalidFieldValueError):
            return ValidationError(
                severity="error",
                message=str(exception),
                location=exception.location,
                error_type="invalid_field_value"
            )
        elif isinstance(exception, BusinessRuleViolation):
            return ValidationError(
                severity="error",
                message=str(exception),
                location=exception.location,
                error_type="business_rule_violation"
            )
        elif isinstance(exception, CanifyValidationError):
            return ValidationError(
                severity="error",
                message=str(exception),
                location=exception.location,
                error_type="validation_error"
            )
        else:
            # 对于未知异常类型，创建通用的 ValidationError
            return ValidationError(
                severity="error",
                message=str(exception),
                error_type="unknown_error"
            )