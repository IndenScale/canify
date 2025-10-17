"""
Canify 验证异常体系

定义验证过程中可能抛出的各种异常类型。
"""

from typing import Optional
from pathlib import Path

from .models import Location


class CanifyValidationError(Exception):
    """Canify 验证错误的基类"""

    def __init__(self, message: str, location: Optional[Location] = None):
        self.message = message
        self.location = location
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        if self.location:
            return f"{self.message} (位置: {self.location})"
        return self.message


class SymbolDiscoveryError(CanifyValidationError):
    """符号发现阶段的错误"""
    pass


class EntityDeclarationError(CanifyValidationError):
    """实体声明相关的错误"""
    pass


class EntityReferenceError(CanifyValidationError):
    """实体引用相关的错误"""
    pass


class SchemaValidationError(CanifyValidationError):
    """数据模型校验相关的错误"""
    pass


# 符号发现阶段的具体异常
class DuplicateEntityIdError(SymbolDiscoveryError):
    """重复的实体ID错误"""

    def __init__(self, entity_id: str, locations: list[Location]):
        self.entity_id = entity_id
        self.locations = locations
        message = f"重复的实体ID: '{entity_id}'"
        super().__init__(message, locations[0] if locations else None)


class InvalidEntityTypeError(SymbolDiscoveryError):
    """无效的实体类型错误"""

    def __init__(self, entity_type: str, location: Optional[Location] = None):
        self.entity_type = entity_type
        message = f"无效的实体类型: '{entity_type}'"
        super().__init__(message, location)


# 实体声明阶段的具体异常
class MissingRequiredFieldError(EntityDeclarationError):
    """缺少必需字段错误"""

    def __init__(self, field_name: str, location: Optional[Location] = None):
        self.field_name = field_name
        message = f"缺少必需字段: '{field_name}'"
        super().__init__(message, location)


class InvalidFieldValueError(EntityDeclarationError):
    """字段值无效错误"""

    def __init__(self, field_name: str, field_value: str, expected_type: str, location: Optional[Location] = None):
        self.field_name = field_name
        self.field_value = field_value
        self.expected_type = expected_type
        message = f"字段 '{field_name}' 的值 '{field_value}' 无效，期望类型: {expected_type}"
        super().__init__(message, location)


# 实体引用阶段的具体异常
class DanglingReferenceError(EntityReferenceError):
    """悬空引用错误"""

    def __init__(self, entity_id: str, location: Optional[Location] = None):
        self.entity_id = entity_id
        message = f"悬空引用: 实体 '{entity_id}' 不存在"
        super().__init__(message, location)


class CircularDependencyError(EntityReferenceError):
    """循环依赖错误"""

    def __init__(self, entity_ids: list[str], location: Optional[Location] = None):
        self.entity_ids = entity_ids
        message = f"检测到循环依赖: {' -> '.join(entity_ids)}"
        super().__init__(message, location)


# 数据模型校验阶段的具体异常
class SchemaConstraintError(SchemaValidationError):
    """数据模型约束错误"""

    def __init__(self, constraint_name: str, message: str, location: Optional[Location] = None):
        self.constraint_name = constraint_name
        full_message = f"数据模型约束 '{constraint_name}' 违反: {message}"
        super().__init__(full_message, location)


class TypeValidationError(SchemaValidationError):
    """类型验证错误"""

    def __init__(self, field_name: str, field_value: str, expected_type: str, location: Optional[Location] = None):
        self.field_name = field_name
        self.field_value = field_value
        self.expected_type = expected_type
        message = f"字段 '{field_name}' 的值 '{field_value}' 类型错误，期望类型: {expected_type}"
        super().__init__(message, location)


# 文件解析相关的异常
class FileParseError(CanifyValidationError):
    """文件解析错误"""

    def __init__(self, file_path: Path, message: str):
        self.file_path = file_path
        full_message = f"文件解析错误 {file_path}: {message}"
        super().__init__(full_message)


class YAMLParsingError(FileParseError):


    """YAML 解析错误"""





    def __init__(self, file_path: Path, yaml_error: str):


        self.yaml_error = yaml_error


        message = f"YAML 解析错误: {yaml_error}"


        super().__init__(file_path, message)








class BusinessRuleViolation(CanifyValidationError):


    """违反业务规则错误"""





    def __init__(self, rule_id: str, message: str, location: Optional[Location] = None):


        self.rule_id = rule_id


        full_message = f"规则 '{self.rule_id}' 校验失败: {message}"


        super().__init__(full_message, location)

