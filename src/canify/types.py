"""
Canify 类型系统定义

提供增强的类型注解，支持实体引用验证和类型约束。
"""

from typing import Annotated, Any
from pydantic.functional_validators import BeforeValidator
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class Ref:
    """
    引用元数据类，用于标注实体引用的目标类型

    Pydantic 不认识这个类，它只是作为元数据存在。
    Canify 验证引擎会在语义分析阶段使用这个信息。
    """

    def __init__(self, entity_type: str):
        """
        初始化引用元数据

        Args:
            entity_type: 目标实体类型，如 "Team", "Project", "Task"
        """
        self.entity_type = entity_type

    def __repr__(self) -> str:
        return f"Ref(entity_type='{self.entity_type}')"


def validate_ref_format(value: Any) -> str:
    """
    验证实体引用格式

    Args:
        value: 要验证的值

    Returns:
        验证通过的字符串值

    Raises:
        ValueError: 当值不是字符串或不以 'entity://' 开头时
    """
    if not isinstance(value, str):
        raise ValueError("实体引用必须是字符串类型")

    if not value.startswith('entity://'):
        raise ValueError(f"实体引用必须以 'entity://' 开头，实际值为: {value}")

    # 提取实体ID部分进行基本验证
    entity_id = value.replace('entity://', '')
    if not entity_id:
        raise ValueError("实体引用不能为空 ID")

    # 基本ID格式验证（可根据需要扩展）
    if ' ' in entity_id:
        raise ValueError(f"实体ID不能包含空格: {entity_id}")

    return value


# 定义 CanifyReference 类型别名
# 这个类型本质上是 str，但在验证前会先运行 validate_ref_format
CanifyReference = Annotated[str, BeforeValidator(validate_ref_format)]


class EntityRef:
    """
    实体引用包装类，提供更丰富的语义信息

    可选的高级功能，用于需要更多上下文的情况
    """

    def __init__(self, ref: str):
        """
        初始化实体引用

        Args:
            ref: 实体引用字符串，格式为 'entity://<entity_id>'
        """
        if not ref.startswith('entity://'):
            raise ValueError(f"无效的实体引用格式: {ref}")

        self.ref = ref
        self.entity_id = ref.replace('entity://', '')

    def __str__(self) -> str:
        return self.ref

    def __repr__(self) -> str:
        return f"EntityRef('{self.ref}')"

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        """
        为 Pydantic 提供核心模式
        """
        return core_schema.no_info_after_validator_function(
            cls._validate,
            handler(str),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, value: Any) -> 'EntityRef':
        """
        Pydantic 验证函数
        """
        if isinstance(value, EntityRef):
            return value
        if isinstance(value, str):
            return cls(value)
        raise ValueError(f"无法将 {type(value)} 转换为 EntityRef")


# 常用引用类型的类型别名，便于使用
TeamRef = Annotated[CanifyReference, Ref("Team")]
ProjectRef = Annotated[CanifyReference, Ref("Project")]
TaskRef = Annotated[CanifyReference, Ref("Task")]
UserRef = Annotated[CanifyReference, Ref("User")]
ServiceRef = Annotated[CanifyReference, Ref("Service")]
DatabaseRef = Annotated[CanifyReference, Ref("Database")]


# 工具函数
def extract_ref_metadata(field_type: Any) -> tuple[str, str | None]:
    """
    从字段类型中提取引用元数据

    Args:
        field_type: 字段的类型注解

    Returns:
        tuple: (基础类型, 目标实体类型) 或 (基础类型, None)
    """
    # 如果是 Annotated 类型，检查是否包含 Ref 元数据
    if hasattr(field_type, '__metadata__') and field_type.__metadata__:
        for metadata in field_type.__metadata__:
            if isinstance(metadata, Ref):
                return str(field_type.__origin__), metadata.entity_type

    # 如果不是引用类型，返回基础类型
    return str(field_type), None


def is_canify_reference(field_type: Any) -> bool:
    """
    检查字段类型是否为 Canify 引用类型
    """
    base_type, target_type = extract_ref_metadata(field_type)
    return target_type is not None
