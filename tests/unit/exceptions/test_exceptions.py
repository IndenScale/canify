"""
异常体系测试
"""

import pytest
from pathlib import Path

from src.core.exceptions import (
    CanifyValidationError,
    DuplicateEntityIdError,
    DanglingReferenceError,
    MissingRequiredFieldError,
    TypeValidationError,
    InvalidFieldValueError,
    BusinessRuleViolation,
    FileParseError,
    YAMLParsingError
)
from src.core.models import Location


class TestExceptions:
    """异常体系测试类"""

    def test_canify_validation_error_base_class(self):
        """测试基础验证错误类"""
        # 测试没有位置信息
        error = CanifyValidationError("测试错误消息")
        assert str(error) == "测试错误消息"
        assert error.message == "测试错误消息"
        assert error.location is None

        # 测试有位置信息
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=10
        )
        error_with_location = CanifyValidationError("测试错误消息", location)
        assert "测试错误消息 (位置: test.md:10)" in str(error_with_location)
        assert error_with_location.location == location

    def test_duplicate_entity_id_error(self):
        """测试重复实体ID错误"""
        locations = [
            Location(file_path=Path("file1.md"), start_line=10, end_line=15),
            Location(file_path=Path("file2.md"), start_line=20, end_line=25)
        ]

        error = DuplicateEntityIdError("duplicate-id", locations)

        assert error.entity_id == "duplicate-id"
        assert error.locations == locations
        assert "重复的实体ID: 'duplicate-id'" in str(error)
        assert error.location == locations[0]  # 使用第一个位置

    def test_dangling_reference_error(self):
        """测试悬空引用错误"""
        location = Location(
            file_path=Path("test.md"),
            start_line=5,
            end_line=5
        )

        error = DanglingReferenceError("non-existent-entity", location)

        assert error.entity_id == "non-existent-entity"
        assert error.location == location
        assert "悬空引用: 实体 'non-existent-entity' 不存在" in str(error)

    def test_missing_required_field_error(self):
        """测试缺少必需字段错误"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        error = MissingRequiredFieldError("name", location)

        assert error.field_name == "name"
        assert error.location == location
        assert "缺少必需字段: 'name'" in str(error)

    def test_type_validation_error(self):
        """测试类型验证错误"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        error = TypeValidationError("budget", "not-a-number", "数字", location)

        assert error.field_name == "budget"
        assert error.field_value == "not-a-number"
        assert error.expected_type == "数字"
        assert error.location == location
        assert "字段 'budget' 的值 'not-a-number' 类型错误，期望类型: 数字" in str(error)

    def test_invalid_field_value_error(self):
        """测试无效字段值错误"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        error = InvalidFieldValueError("status", "invalid-status", "有效值: active, inactive", location)

        assert error.field_name == "status"
        assert error.field_value == "invalid-status"
        assert error.expected_type == "有效值: active, inactive"
        assert error.location == location
        assert "字段 'status' 的值 'invalid-status' 无效，期望类型: 有效值: active, inactive" in str(error)

    def test_business_rule_violation(self):
        """测试业务规则违反错误"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        error = BusinessRuleViolation("project-singleton", "项目中只能有一个 project 实体", location)

        assert error.rule_id == "project-singleton"
        assert error.location == location
        assert "规则 'project-singleton' 校验失败: 项目中只能有一个 project 实体" in str(error)

    def test_file_parse_error(self):
        """测试文件解析错误"""
        file_path = Path("test.md")
        error = FileParseError(file_path, "文件格式错误")

        assert error.file_path == file_path
        assert "文件解析错误 test.md: 文件格式错误" in str(error)

    def test_yaml_parsing_error(self):
        """测试 YAML 解析错误"""
        file_path = Path("test.md")
        yaml_error = "mapping values are not allowed here"
        error = YAMLParsingError(file_path, yaml_error)

        assert error.file_path == file_path
        assert error.yaml_error == yaml_error
        assert "YAML 解析错误: mapping values are not allowed here" in str(error)

    def test_exception_inheritance_hierarchy(self):
        """测试异常继承层次"""
        # 验证继承关系
        assert issubclass(DuplicateEntityIdError, CanifyValidationError)
        assert issubclass(DanglingReferenceError, CanifyValidationError)
        assert issubclass(MissingRequiredFieldError, CanifyValidationError)
        assert issubclass(TypeValidationError, CanifyValidationError)
        assert issubclass(InvalidFieldValueError, CanifyValidationError)
        assert issubclass(BusinessRuleViolation, CanifyValidationError)
        assert issubclass(FileParseError, CanifyValidationError)
        assert issubclass(YAMLParsingError, FileParseError)

    def test_exception_without_location(self):
        """测试没有位置信息的异常"""
        # 测试各种异常在没有位置信息时的行为
        errors = [
            DuplicateEntityIdError("test-id", []),
            DanglingReferenceError("test-entity", None),
            MissingRequiredFieldError("test-field", None),
            TypeValidationError("test-field", "value", "expected", None),
            InvalidFieldValueError("test-field", "value", "expected", None),
            BusinessRuleViolation("test-rule", "message", None)
        ]

        for error in errors:
            assert error.location is None
            # 应该能够正常转换为字符串
            assert isinstance(str(error), str)
            assert len(str(error)) > 0

    def test_multiple_locations_in_duplicate_error(self):
        """测试重复错误中的多个位置"""
        locations = [
            Location(file_path=Path("file1.md"), start_line=10, end_line=15),
            Location(file_path=Path("file2.md"), start_line=20, end_line=25),
            Location(file_path=Path("file3.md"), start_line=30, end_line=35)
        ]

        error = DuplicateEntityIdError("multi-location-id", locations)

        assert len(error.locations) == 3
        assert error.location == locations[0]  # 使用第一个位置

    def test_error_message_formatting(self):
        """测试错误消息格式化"""
        # 测试各种错误消息格式
        test_cases = [
            (CanifyValidationError("简单错误"), "简单错误"),
            (CanifyValidationError("带位置错误", Location(file_path=Path("test.md"), start_line=10, end_line=10)), "带位置错误 (位置: test.md:10)"),
            (DuplicateEntityIdError("dup-id", [Location(file_path=Path("test.md"), start_line=10, end_line=10)]), "重复的实体ID: 'dup-id'"),
            (DanglingReferenceError("dangling-id", Location(file_path=Path("test.md"), start_line=5, end_line=5)), "悬空引用: 实体 'dangling-id' 不存在"),
        ]

        for error, expected_prefix in test_cases:
            error_str = str(error)
            assert expected_prefix in error_str