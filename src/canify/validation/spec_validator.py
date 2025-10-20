"""
Spec 验证器

负责验证 spec 规则中的 fixture 和 test_case 引用是否有效。
"""

import logging
import importlib
from typing import List, Optional, Callable, Any
from pathlib import Path

from ..models.spec import SpecificationRule
from ..models.validation_result import ValidationResult, ValidationError, ValidationSeverity

logger = logging.getLogger(__name__)


class SpecValidator:
    """Spec 验证器"""

    def __init__(self, project_root: Path):
        """
        初始化验证器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)

    def validate_spec(self, spec: SpecificationRule) -> ValidationResult:
        """
        验证单个 spec 规则

        Args:
            spec: 要验证的 spec 规则

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        # 验证 fixture
        if spec.fixture:
            fixture_result = self._validate_fixture(spec)
            result.merge(fixture_result)

        # 验证 test_case
        if spec.test_case:
            test_case_result = self._validate_test_case(spec)
            result.merge(test_case_result)

        return result

    def validate_specs(self, specs: List[SpecificationRule]) -> ValidationResult:
        """
        验证多个 spec 规则

        Args:
            specs: 要验证的 spec 规则列表

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        for spec in specs:
            spec_result = self.validate_spec(spec)
            result.merge(spec_result)

        return result

    def _validate_fixture(self, spec: SpecificationRule) -> ValidationResult:
        """
        验证 fixture 引用

        Args:
            spec: spec 规则

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        try:
            fixture_func = self._import_function(spec.fixture)
            if not fixture_func:
                result.add_error(
                    ValidationError(
                        rule_id=spec.id,
                        message=f"无法找到 fixture 函数: {spec.fixture}",
                        severity=ValidationSeverity.ERROR,
                        location=None
                    )
                )
                return result

            # 检查函数是否有 canify.fixture 装饰器
            if not hasattr(fixture_func, '_canify_fixture'):
                result.add_warning(
                    ValidationError(
                        rule_id=spec.id,
                        message=f"fixture 函数 {spec.fixture} 未使用 @canify.fixture 装饰器",
                        severity=ValidationSeverity.WARNING,
                        location=None
                    )
                )

        except Exception as e:
            result.add_error(
                ValidationError(
                    rule_id=spec.id,
                    message=f"验证 fixture {spec.fixture} 失败: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    location=None
                )
            )

        return result

    def _validate_test_case(self, spec: SpecificationRule) -> ValidationResult:
        """
        验证 test_case 引用

        Args:
            spec: spec 规则

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        try:
            test_case_func = self._import_function(spec.test_case)
            if not test_case_func:
                result.add_error(
                    ValidationError(
                        rule_id=spec.id,
                        message=f"无法找到 test_case 函数: {spec.test_case}",
                        severity=ValidationSeverity.ERROR,
                        location=None
                    )
                )
                return result

            # 检查函数是否有 canify.test_case 装饰器
            if not hasattr(test_case_func, '_canify_test_case'):
                result.add_warning(
                    ValidationError(
                        rule_id=spec.id,
                        message=f"test_case 函数 {spec.test_case} 未使用 @canify.test_case 装饰器",
                        severity=ValidationSeverity.WARNING,
                        location=None
                    )
                )

        except Exception as e:
            result.add_error(
                ValidationError(
                    rule_id=spec.id,
                    message=f"验证 test_case {spec.test_case} 失败: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    location=None
                )
            )

        return result

    def _import_function(self, function_path: str) -> Optional[Callable[..., Any]]:
        """
        根据函数路径导入函数

        Args:
            function_path: 函数路径，格式为 "module.function_name"

        Returns:
            函数对象，如果导入失败则返回 None
        """
        try:
            # 分割模块路径和函数名
            parts = function_path.split('.')
            if len(parts) < 2:
                return None

            module_name = '.'.join(parts[:-1])
            function_name = parts[-1]

            # 导入模块
            module = importlib.import_module(module_name)

            # 获取函数
            func = getattr(module, function_name, None)
            return func

        except ImportError:
            logger.warning(f"无法导入模块: {module_name}")
            return None
        except AttributeError:
            logger.warning(f"模块 {module_name} 中没有函数: {function_name}")
            return None
        except Exception as e:
            logger.warning(f"导入函数 {function_path} 失败: {e}")
            return None

    def get_fixture_function(self, spec: SpecificationRule) -> Optional[Callable[..., Any]]:
        """
        获取 spec 的 fixture 函数

        Args:
            spec: spec 规则

        Returns:
            fixture 函数，如果获取失败则返回 None
        """
        if not spec.fixture:
            return None

        return self._import_function(spec.fixture)

    def get_test_case_function(self, spec: SpecificationRule) -> Optional[Callable[..., Any]]:
        """
        获取 spec 的 test_case 函数

        Args:
            spec: spec 规则

        Returns:
            test_case 函数，如果获取失败则返回 None
        """
        if not spec.test_case:
            return None

        return self._import_function(spec.test_case)