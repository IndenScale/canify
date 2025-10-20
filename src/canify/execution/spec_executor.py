"""
Spec 执行器

负责执行 spec 规则的验证逻辑。
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

from ..models.spec import SpecificationRule
from ..models.validation_result import ValidationResult, ValidationError, ValidationSeverity
from ..validation.spec_validator import SpecValidator

logger = logging.getLogger(__name__)


class SpecExecutor:
    """Spec 执行器"""

    def __init__(self, project_root: Path):
        """
        初始化执行器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.spec_validator = SpecValidator(project_root)

    def execute_specs(self, specs: List[SpecificationRule]) -> ValidationResult:
        """
        执行多个 spec 规则的验证

        Args:
            specs: spec 规则列表

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        for spec in specs:
            spec_result = self.execute_single_spec(spec)
            result.merge(spec_result)

        logger.info(f"执行了 {len(specs)} 个 spec 规则，成功: {result.success}, 错误: {len(result.errors)}, 警告: {len(result.warnings)}")
        return result

    def execute_single_spec(self, spec: SpecificationRule) -> ValidationResult:
        """
        执行单个 spec 规则的验证

        Args:
            spec: spec 规则

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        try:
            # 1. 验证 fixture 和 test_case
            validation_result = self.spec_validator.validate_spec(spec)
            if not validation_result.success:
                result.merge(validation_result)
                return result

            # 2. 获取 fixture 数据
            fixture_data = self._get_fixture_data(spec)
            if fixture_data is None:
                result.add_error(
                    ValidationError(
                        rule_id=spec.id,
                        message=f"无法获取 fixture 数据: {spec.fixture}",
                        severity=ValidationSeverity.ERROR,
                        location=None
                    )
                )
                return result

            # 3. 执行 test_case
            test_result = self._execute_test_case(spec, fixture_data)
            result.merge(test_result)

        except Exception as e:
            result.add_error(
                ValidationError(
                    rule_id=spec.id,
                    message=f"执行 spec 规则失败: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    location=None
                )
            )

        return result

    def _get_fixture_data(self, spec: SpecificationRule) -> Any:
        """
        获取 fixture 数据

        Args:
            spec: spec 规则

        Returns:
            fixture 数据
        """
        if not spec.fixture:
            return None

        try:
            fixture_func = self.spec_validator.get_fixture_function(spec)
            if not fixture_func:
                return None

            # 执行 fixture 函数
            return fixture_func()

        except Exception as e:
            logger.error(f"执行 fixture {spec.fixture} 失败: {e}")
            return None

    def _execute_test_case(self, spec: SpecificationRule, fixture_data: Any) -> ValidationResult:
        """
        执行 test_case

        Args:
            spec: spec 规则
            fixture_data: fixture 数据

        Returns:
            验证结果
        """
        result = ValidationResult.success_result()

        if not spec.test_case:
            # 如果没有 test_case，则跳过
            return result

        try:
            test_case_func = self.spec_validator.get_test_case_function(spec)
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

            # 执行 test_case 函数
            test_result = test_case_func(fixture_data)

            # 处理测试结果
            if isinstance(test_result, bool):
                if not test_result:
                    result.add_error(
                        ValidationError(
                            rule_id=spec.id,
                            message=f"测试用例失败: {spec.test_case}",
                            severity=ValidationSeverity.ERROR,
                            location=None
                        )
                    )
            elif isinstance(test_result, ValidationResult):
                result.merge(test_result)
            elif test_result is not None:
                # 其他类型的返回值视为成功
                pass

        except Exception as e:
            result.add_error(
                ValidationError(
                    rule_id=spec.id,
                    message=f"执行 test_case {spec.test_case} 失败: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    location=None
                )
            )

        return result

    def execute_specs_with_env_filter(
        self,
        specs: List[SpecificationRule],
        env: str = "local"
    ) -> ValidationResult:
        """
        根据执行环境过滤并执行 spec 规则

        Args:
            specs: spec 规则列表
            env: 执行环境 (local 或 remote)

        Returns:
            验证结果
        """
        # 过滤 spec 规则
        filtered_specs = [spec for spec in specs if spec.env == env or spec.env == "all"]

        logger.info(f"根据环境 '{env}' 过滤了 {len(filtered_specs)}/{len(specs)} 个 spec 规则")

        # 执行过滤后的规则
        return self.execute_specs(filtered_specs)