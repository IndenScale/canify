"""
验证结果模型测试
"""

import pytest
from pathlib import Path

from src.core.models import ValidationResult, ValidationError, Location


class TestValidationResult:
    """验证结果模型测试类"""

    def test_create_validation_result(self):
        """测试创建验证结果"""
        result = ValidationResult(success=True)

        assert result.success is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_errors_and_warnings(self):
        """测试添加错误和警告"""
        result = ValidationResult(success=True)

        # 创建错误和警告
        error_location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=10
        )

        warning_location = Location(
            file_path=Path("test.md"),
            start_line=15,
            end_line=15
        )

        error = ValidationError(
            severity="error",
            message="测试错误",
            location=error_location,
            entity_id="test-entity",
            error_type="TestError"
        )

        warning = ValidationError(
            severity="warning",
            message="测试警告",
            location=warning_location,
            entity_id="test-entity",
            error_type="TestWarning"
        )

        # 添加错误和警告
        result.add_error(error)
        result.add_warning(warning)

        # 验证添加结果
        assert result.success is False  # 添加错误后应该失败
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert result.errors[0] == error
        assert result.warnings[0] == warning

    def test_total_issues_calculation(self):
        """测试问题总数计算"""
        result = ValidationResult(success=True)

        # 初始状态
        assert result.total_issues == 0

        # 添加错误
        error = ValidationError(
            severity="error",
            message="错误1",
            error_type="Error1"
        )
        result.add_error(error)
        assert result.total_issues == 1

        # 添加警告
        warning = ValidationError(
            severity="warning",
            message="警告1",
            error_type="Warning1"
        )
        result.add_warning(warning)
        assert result.total_issues == 2

        # 添加更多错误和警告
        error2 = ValidationError(
            severity="error",
            message="错误2",
            error_type="Error2"
        )
        warning2 = ValidationError(
            severity="warning",
            message="警告2",
            error_type="Warning2"
        )

        result.add_error(error2)
        result.add_warning(warning2)

        assert result.total_issues == 4

    def test_error_string_representation(self):
        """测试错误字符串表示"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=10
        )

        error = ValidationError(
            severity="error",
            message="测试错误消息",
            location=location,
            entity_id="test-entity",
            error_type="TestError"
        )

        expected_str = "[ERROR] TestError: 测试错误消息 at test.md:10"
        assert str(error) == expected_str

    def test_error_without_location(self):
        """测试没有位置信息的错误"""
        error = ValidationError(
            severity="error",
            message="测试错误消息",
            error_type="TestError"
        )

        expected_str = "[ERROR] TestError: 测试错误消息 at unknown location"
        assert str(error) == expected_str

    def test_validation_result_with_symbol_table(self):
        """测试包含符号表的验证结果"""
        from src.core.models import SymbolTable

        symbol_table = SymbolTable()
        result = ValidationResult(
            success=True,
            symbol_table=symbol_table
        )

        assert result.symbol_table == symbol_table

    def test_multiple_errors_and_warnings(self):
        """测试多个错误和警告"""
        result = ValidationResult(success=True)

        # 添加多个错误
        for i in range(3):
            error = ValidationError(
                severity="error",
                message=f"错误 {i+1}",
                error_type=f"Error{i+1}"
            )
            result.add_error(error)

        # 添加多个警告
        for i in range(2):
            warning = ValidationError(
                severity="warning",
                message=f"警告 {i+1}",
                error_type=f"Warning{i+1}"
            )
            result.add_warning(warning)

        assert len(result.errors) == 3
        assert len(result.warnings) == 2
        assert result.total_issues == 5
        assert result.success is False

    def test_error_with_column_location(self):
        """测试包含列位置信息的错误"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=15
        )

        error = ValidationError(
            severity="error",
            message="测试错误",
            location=location,
            error_type="TestError"
        )

        expected_str = "[ERROR] TestError: 测试错误 at test.md:10:5-10:15"
        assert str(error) == expected_str

    def test_error_with_range_location(self):
        """测试包含范围位置信息的错误"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        error = ValidationError(
            severity="error",
            message="测试错误",
            location=location,
            error_type="TestError"
        )

        expected_str = "[ERROR] TestError: 测试错误 at test.md:10-15"
        assert str(error) == expected_str