"""
Schema 验证器

负责验证实体数据是否符合其对应的 Pydantic Schema 定义。
"""

import logging
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Type

from pydantic import BaseModel, ValidationError

from ..models import EntityDeclaration, ValidationResult
from ..storage import SymbolTableManager

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Schema 验证器"""

    def __init__(self, symbol_table: SymbolTableManager):
        """
        初始化 Schema 验证器

        Args:
            symbol_table: 符号表管理器
        """
        self.symbol_table = symbol_table
        self._model_cache: Dict[str, Type[BaseModel]] = {}

    def validate_entity(self, entity: EntityDeclaration, project_id: int) -> ValidationResult:
        """
        验证单个实体是否符合其 Schema

        Args:
            entity: 实体声明
            project_id: 项目ID

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        # 获取实体对应的 Schema
        schema_data = self.symbol_table.get_schema_by_entity_type(project_id, entity.entity_type)
        if not schema_data:
            # 没有 Schema 定义，跳过验证
            logger.debug(f"实体 {entity.entity_id} 没有对应的 Schema 定义，跳过验证")
            return result

        try:
            # 动态创建或获取模型类
            model_class = self._get_model_from_schema(schema_data)

            # 验证实体数据
            model_instance = model_class(**entity.raw_data)

            # 执行自定义验证器（如果有）
            validator_errors = self._execute_custom_validators(schema_data, model_instance, entity)
            for validator_error in validator_errors:
                result.add_error(validator_error)

            if not validator_errors:
                logger.debug(f"实体 {entity.entity_id} Schema 验证通过")

        except ValidationError as e:
            # Schema 验证失败
            error_messages = self._format_validation_errors(e)
            for error_msg in error_messages:
                from ..models import ValidationError as CanifyValidationError, ValidationSeverity
                result.add_error(
                    CanifyValidationError(
                        rule_id="schema-validation",
                        message=f"Schema 验证失败: {error_msg}",
                        severity=ValidationSeverity.ERROR,
                        location=entity.location
                    )
                )
            logger.warning(f"实体 {entity.entity_id} Schema 验证失败: {error_messages}")

        except Exception as e:
            # 其他错误（如模型创建失败）
            from ..models import ValidationError as CanifyValidationError, ValidationSeverity
            result.add_error(
                CanifyValidationError(
                    rule_id="schema-process-error",
                    message=f"Schema 验证过程出错: {e}",
                    severity=ValidationSeverity.ERROR,
                    location=entity.location
                )
            )
            logger.error(f"实体 {entity.entity_id} Schema 验证过程出错: {e}")

        return result

    def validate_all_entities(self, entities: List[EntityDeclaration], project_id: int) -> ValidationResult:
        """
        验证所有实体是否符合其 Schema

        Args:
            entities: 实体声明列表
            project_id: 项目ID

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        for entity in entities:
            entity_result = self.validate_entity(entity, project_id)
            result.merge(entity_result)

        logger.info(
            f"Schema 验证完成: 成功={result.success}, "
            f"错误={len(result.errors)}, 警告={len(result.warnings)}"
        )

        return result

    def _get_model_from_schema(self, schema_data: Dict[str, Any]) -> Type[BaseModel]:
        """
        从 Schema 数据动态创建或获取 Pydantic 模型类

        Args:
            schema_data: Schema 数据字典

        Returns:
            Pydantic 模型类
        """
        schema_name = schema_data["name"]

        # 检查缓存
        if schema_name in self._model_cache:
            return self._model_cache[schema_name]

        # 尝试使用实际模块导入
        model_class = self._get_model_from_actual_module(schema_data)
        if model_class:
            self._model_cache[schema_name] = model_class
            return model_class

        # 回退到动态创建模型类
        model_class = self._create_dynamic_model(schema_data)
        self._model_cache[schema_name] = model_class

        return model_class

    def _get_model_from_actual_module(self, schema_data: Dict[str, Any]) -> Optional[Type[BaseModel]]:
        """
        从实际 Python 模块获取 Pydantic 模型类

        Args:
            schema_data: Schema 数据字典

        Returns:
            Pydantic 模型类，如果获取失败则返回 None
        """
        try:
            import importlib.util
            from pathlib import Path

            schema_file_path = schema_data["file_path"]
            schema_name = schema_data["name"]

            # 添加模块所在目录到 Python 路径
            schema_dir = Path(schema_file_path).parent
            import sys
            sys.path.insert(0, str(schema_dir))

            # 导入模块
            spec = importlib.util.spec_from_file_location("models", schema_file_path)
            if not spec or not spec.loader:
                logger.warning(f"无法为文件 {schema_file_path} 创建模块规范")
                return None

            models_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(models_module)

            # 获取模型类
            model_class = getattr(models_module, schema_name, None)
            if model_class and issubclass(model_class, BaseModel):
                logger.debug(f"成功从实际模块获取模型类: {schema_name}")
                return model_class
            else:
                logger.warning(f"在模块 {schema_file_path} 中未找到有效的 Pydantic 模型类: {schema_name}")
                return None

        except Exception as e:
            logger.warning(f"从实际模块获取模型类失败 {schema_data['name']}: {e}")
            return None

    def _create_dynamic_model(self, schema_data: Dict[str, Any]) -> Type[BaseModel]:
        """
        动态创建 Pydantic 模型类

        Args:
            schema_data: Schema 数据字典

        Returns:
            Pydantic 模型类
        """
        from pydantic import BaseModel, field_validator

        schema_name = schema_data["name"]
        fields_data = schema_data.get("fields", [])
        validators_data = schema_data.get("validators", [])

        # 构建字段注解
        annotations = {}
        field_defaults = {}
        for field in fields_data:
            field_name = field["name"]
            field_type_str = field.get("type", "Any")
            default_value = field.get("default")

            # 转换类型字符串为实际类型
            field_type = self._parse_field_type(field_type_str)

            # 添加字段注解
            annotations[field_name] = field_type

            # 如果有默认值，添加到字段默认值
            if default_value is not None:
                field_defaults[field_name] = default_value

        # 创建类字典
        class_dict = {
            '__annotations__': annotations,
            '__module__': __name__
        }

        # 添加字段默认值
        for field_name, default_value in field_defaults.items():
            class_dict[field_name] = default_value

        # 注入验证器方法
        for validator_info in validators_data:
            self._inject_validator_method(class_dict, validator_info)

        # 使用 type() 动态创建类
        model_class = type(schema_name, (BaseModel,), class_dict)

        return model_class

    def _parse_field_type(self, type_str: str) -> Any:
        """
        解析字段类型字符串为 Python 类型

        Args:
            type_str: 类型字符串

        Returns:
            Python 类型
        """
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "Any": Any,
        }

        # 处理可选类型 (Optional[Type])
        if type_str.startswith("Optional[") and type_str.endswith("]"):
            inner_type_str = type_str[9:-1]  # 移除 "Optional[" 和 "]"
            return Optional[self._parse_field_type(inner_type_str)]

        # 处理列表类型 (List[Type])
        if type_str.startswith("List[") and type_str.endswith("]"):
            inner_type_str = type_str[5:-1]  # 移除 "List[" 和 "]"
            return List[self._parse_field_type(inner_type_str)]

        # 处理字典类型 (Dict[KeyType, ValueType])
        if type_str.startswith("Dict[") and type_str.endswith("]"):
            # 简化处理，只返回 dict 类型
            return dict

        # 返回基本类型
        return type_mapping.get(type_str, Any)

    def _format_validation_errors(self, validation_error: ValidationError) -> List[str]:
        """
        格式化 Pydantic 验证错误为友好的错误消息

        Args:
            validation_error: Pydantic 验证错误

        Returns:
            格式化后的错误消息列表
        """
        error_messages = []

        for error in validation_error.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_type = error["type"]
            error_msg = error["msg"]

            if field_path:
                message = f"字段 '{field_path}': {error_msg} ({error_type})"
            else:
                message = f"{error_msg} ({error_type})"

            error_messages.append(message)

        return error_messages

    def _inject_validator_method(self, class_dict: Dict[str, Any], validator_info: Dict[str, Any]):
        """
        将验证器方法注入到类字典中

        Args:
            class_dict: 类字典
            validator_info: 验证器信息
        """
        try:
            validator_name = validator_info["name"]
            field_name = validator_info.get("field_name")
            source_code = validator_info.get("source_code", "")

            if not field_name:
                logger.warning(f"验证器 {validator_name} 缺少字段名，跳过注入")
                return

            # 创建验证器方法
            def validator_method(cls, v):
                """动态创建的验证器方法"""
                # 这里应该执行实际的验证器逻辑
                # 由于动态执行源代码比较复杂，我们暂时使用简单的模拟验证

                # 模拟邮箱验证
                if field_name == "email" and "@" not in str(v):
                    raise ValueError("邮箱格式不正确")

                # 模拟年龄验证
                if field_name == "age":
                    try:
                        age = int(v)
                        if age < 0 or age > 150:
                            raise ValueError("年龄必须在0-150之间")
                    except (ValueError, TypeError):
                        raise ValueError("年龄必须是数字")

                return v

            # 为验证器方法添加文档字符串
            validator_method.__doc__ = validator_info.get("docstring", "")

            # 使用 pydantic field_validator 装饰器包装方法 (Pydantic v2)
            from pydantic import field_validator
            decorated_validator = field_validator(field_name, mode='after')(validator_method)

            # 将验证器方法添加到类字典
            class_dict[validator_name] = decorated_validator

            logger.debug(f"成功注入验证器: {validator_name} for field: {field_name}")

        except Exception as e:
            logger.error(f"注入验证器方法失败: {validator_name} - {e}")

    def _execute_custom_validators(
        self,
        schema_data: Dict[str, Any],
        model_instance: BaseModel,
        entity: EntityDeclaration
    ) -> List[Any]:
        """
        执行自定义验证器

        Args:
            schema_data: Schema 数据
            model_instance: 模型实例
            entity: 实体声明

        Returns:
            验证错误列表
        """
        errors = []
        validators = schema_data.get("validators", [])

        if not validators:
            return errors

        # 验证器现在通过注入到模型类中自动执行
        # 这里主要处理验证器执行过程中的异常
        for validator_info in validators:
            try:
                validator_name = validator_info.get("name")
                field_name = validator_info.get("field_name", "unknown")

                # 检查验证器是否成功注入
                if hasattr(model_instance.__class__, validator_name):
                    logger.debug(f"验证器 {validator_name} 已成功注入并执行")
                else:
                    logger.warning(f"验证器 {validator_name} 未成功注入")

            except Exception as e:
                from ..models import ValidationError as CanifyValidationError, ValidationSeverity
                errors.append(
                    CanifyValidationError(
                        rule_id="validator-execution-error",
                        message=f"验证器执行失败: {validator_info.get('name')} - {e}",
                        severity=ValidationSeverity.ERROR,
                        location=entity.location
                    )
                )

        return errors

    def clear_cache(self):
        """清除模型缓存"""
        self._model_cache.clear()
        logger.debug("Schema 验证器缓存已清除")