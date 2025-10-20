"""
Canify 核心概念模型

定义了 Canify 系统中所有组件共享的核心数据结构。
这些模型是 CLI 和 Server 之间通信的数据契约。
"""
from .location import Location
from .entity_declaration import EntityDeclaration
from .entity_reference import EntityReference
from .spec import SpecificationRule
from .view import View
from .validation_result import ValidationResult, ValidationError, ValidationSeverity

__all__ = [
    "Location",
    "EntityDeclaration",
    "EntityReference",
    "SpecificationRule",
    "View",
    "ValidationResult",
    "ValidationError",
    "ValidationSeverity",
]
