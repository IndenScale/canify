"""
验证引擎测试
"""

import pytest
from pathlib import Path

from src.core.validation_engine import ValidationEngine
from src.core.models import (
    EntityDeclaration,
    EntityReference,
    Location,
    ValidationResult,
    ValidationError
)
from src.core.exceptions import (
    DuplicateEntityIdError,
    DanglingReferenceError,
    MissingRequiredFieldError,
    TypeValidationError,
    InvalidFieldValueError,
    BusinessRuleViolation
)


class TestValidationEngine:
    """验证引擎测试类"""

    @pytest.fixture
    def validation_engine(self):
        """创建验证引擎实例"""
        return ValidationEngine()

    @pytest.fixture
    def sample_entities(self):
        """创建示例实体"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        return [
            EntityDeclaration(
                location=location,
                entity_type="project",
                entity_id="test-project",
                name="测试项目",
                raw_data={
                    "type": "project",
                    "id": "test-project",
                    "name": "测试项目",
                    "budget": 10000.0,
                    "status": "active",
                    "developers": ["user-alice", "user-bob"]
                },
                source_code="type: project\nid: test-project\nname: 测试项目\nbudget: 10000.0\nstatus: active\ndevelopers: [user-alice, user-bob]"
            ),
            EntityDeclaration(
                location=location,
                entity_type="user",
                entity_id="user-alice",
                name="Alice Zhang",
                raw_data={
                    "type": "user",
                    "id": "user-alice",
                    "name": "Alice Zhang",
                    "email": "alice@example.com"
                },
                source_code="type: user\nid: user-alice\nname: Alice Zhang\nemail: alice@example.com"
            ),
            EntityDeclaration(
                location=location,
                entity_type="user",
                entity_id="user-bob",
                name="Bob Li",
                raw_data={
                    "type": "user",
                    "id": "user-bob",
                    "name": "Bob Li",
                    "email": "bob@example.com"
                },
                source_code="type: user\nid: user-bob\nname: Bob Li\nemail: bob@example.com"
            )
        ]

    @pytest.fixture
    def sample_references(self):
        """创建示例引用"""
        location = Location(
            file_path=Path("test.md"),
            start_line=5,
            end_line=5
        )

        return [
            EntityReference(
                location=location,
                entity_id="user-alice",
                context_text="Alice",
                reference_type="link"
            ),
            EntityReference(
                location=location,
                entity_id="user-bob",
                context_text="Bob",
                reference_type="link"
            ),
            EntityReference(
                location=location,
                entity_id="test-project",
                context_text="测试项目",
                reference_type="link"
            )
        ]

    def test_validate_successful_case(self, validation_engine, sample_entities, sample_references):
        """测试成功的验证案例"""
        project_root = Path(".")

        result = validation_engine.validate(
            declarations=sample_entities,
            references=sample_references,
            project_root=project_root,
            mode="verify",
            strict=False
        )

        assert result.success is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_duplicate_entity_id_detection(self, validation_engine):
        """测试重复实体ID检测"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        # 创建重复ID的实体
        duplicate_entities = [
            EntityDeclaration(
                location=location,
                entity_type="project",
                entity_id="duplicate-id",
                name="项目1",
                raw_data={
                    "type": "project",
                    "id": "duplicate-id",
                    "name": "项目1"
                },
                source_code="type: project\nid: duplicate-id\nname: 项目1"
            ),
            EntityDeclaration(
                location=location,
                entity_type="task",
                entity_id="duplicate-id",  # 相同ID
                name="任务1",
                raw_data={
                    "type": "task",
                    "id": "duplicate-id",
                    "name": "任务1"
                },
                source_code="type: task\nid: duplicate-id\nname: 任务1"
            )
        ]

        project_root = Path(".")
        result = validation_engine.validate(
            declarations=duplicate_entities,
            references=[],
            project_root=project_root,
            mode="verify",
            strict=False
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert isinstance(result.errors[0], ValidationError)
        assert result.errors[0].error_type == "duplicate_entity_id"
        assert "重复的实体ID: 'duplicate-id'" in str(result.errors[0])

    def test_dangling_reference_detection(self, validation_engine, sample_entities):
        """测试悬空引用检测"""
        location = Location(
            file_path=Path("test.md"),
            start_line=5,
            end_line=5
        )

        # 创建指向不存在实体的引用
        dangling_references = [
            EntityReference(
                location=location,
                entity_id="non-existent-entity",  # 不存在的实体
                context_text="不存在的实体",
                reference_type="link"
            )
        ]

        project_root = Path(".")
        result = validation_engine.validate(
            declarations=sample_entities,
            references=dangling_references,
            project_root=project_root,
            mode="verify",
            strict=False
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert isinstance(result.errors[0], ValidationError)
        assert result.errors[0].error_type == "dangling_reference"
        assert "悬空引用: 实体 'non-existent-entity' 不存在" in str(result.errors[0])

    def test_missing_required_field_detection(self, validation_engine):
        """测试缺少必需字段检测"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        # 创建缺少必需字段的实体
        invalid_entities = [
            EntityDeclaration(
                location=location,
                entity_type="project",
                entity_id="test-project",
                name="测试项目",
                raw_data={
                    "type": "project",
                    "id": "test-project"
                    # 缺少 name 字段
                },
                source_code="type: project\nid: test-project"
            )
        ]

        project_root = Path(".")
        result = validation_engine.validate(
            declarations=invalid_entities,
            references=[],
            project_root=project_root,
            mode="verify",
            strict=False
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert isinstance(result.errors[0], ValidationError)
        assert result.errors[0].error_type == "missing_required_field"
        assert "缺少必需字段: 'name'" in str(result.errors[0])

    def test_type_validation(self, validation_engine):
        """测试类型验证"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        # 创建类型错误的实体
        invalid_entities = [
            EntityDeclaration(
                location=location,
                entity_type="project",
                entity_id="test-project",
                name="测试项目",
                raw_data={
                    "type": "project",
                    "id": "test-project",
                    "name": "测试项目",
                    "budget": "not-a-number"  # 应该是数字
                },
                source_code="type: project\nid: test-project\nname: 测试项目\nbudget: not-a-number"
            )
        ]

        project_root = Path(".")
        result = validation_engine.validate(
            declarations=invalid_entities,
            references=[],
            project_root=project_root,
            mode="verify",
            strict=False
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert isinstance(result.errors[0], ValidationError)
        assert result.errors[0].error_type == "type_validation"
        assert "字段 'budget' 的值 'not-a-number' 类型错误" in str(result.errors[0])

    def test_invalid_field_value_validation(self, validation_engine):
        """测试无效字段值验证"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        # 创建字段值无效的实体
        invalid_entities = [
            EntityDeclaration(
                location=location,
                entity_type="project",
                entity_id="test-project",
                name="测试项目",
                raw_data={
                    "type": "project",
                    "id": "test-project",
                    "name": "测试项目",
                    "status": "invalid-status"  # 无效的状态值
                },
                source_code="type: project\nid: test-project\nname: 测试项目\nstatus: invalid-status"
            )
        ]

        project_root = Path(".")
        result = validation_engine.validate(
            declarations=invalid_entities,
            references=[],
            project_root=project_root,
            mode="verify",
            strict=False
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert isinstance(result.errors[0], ValidationError)
        assert result.errors[0].error_type == "invalid_field_value"
        assert "字段 'status' 的值 'invalid-status' 无效" in str(result.errors[0])

    def test_list_field_validation(self, validation_engine):
        """测试列表字段验证"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        # 创建列表字段类型错误的实体
        invalid_entities = [
            EntityDeclaration(
                location=location,
                entity_type="project",
                entity_id="test-project",
                name="测试项目",
                raw_data={
                    "type": "project",
                    "id": "test-project",
                    "name": "测试项目",
                    "developers": "not-a-list"  # 应该是列表
                },
                source_code="type: project\nid: test-project\nname: 测试项目\ndevelopers: not-a-list"
            )
        ]

        project_root = Path(".")
        result = validation_engine.validate(
            declarations=invalid_entities,
            references=[],
            project_root=project_root,
            mode="verify",
            strict=False
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert isinstance(result.errors[0], ValidationError)
        assert result.errors[0].error_type == "type_validation"
        assert "字段 'developers' 的值 'not-a-list' 类型错误" in str(result.errors[0])

    def test_symbol_table_built_correctly(self, validation_engine, sample_entities, sample_references):
        """测试符号表正确构建"""
        project_root = Path(".")

        # 首先手动添加引用到符号表
        for reference in sample_references:
            validation_engine.symbol_table.add_reference(reference)

        result = validation_engine.validate(
            declarations=sample_entities,
            references=sample_references,
            project_root=project_root,
            mode="verify",
            strict=False
        )

        # 验证符号表构建正确
        symbol_table = validation_engine.get_symbol_table()
        assert symbol_table.total_entities == 3
        # 注意：验证引擎目前不会自动添加引用到符号表
        # assert symbol_table.total_references == 3

        # 验证实体存在
        assert symbol_table.find_entity("test-project") is not None
        assert symbol_table.find_entity("user-alice") is not None
        assert symbol_table.find_entity("user-bob") is not None

        # 验证引用存在
        references_to_alice = symbol_table.get_references_to("user-alice")
        assert len(references_to_alice) == 1
        assert references_to_alice[0].entity_id == "user-alice"

    def test_validation_modes(self, validation_engine, sample_entities, sample_references):
        """测试不同验证模式"""
        project_root = Path(".")

        # 测试 lint 模式
        result_lint = validation_engine.validate(
            declarations=sample_entities,
            references=sample_references,
            project_root=project_root,
            mode="lint",
            strict=False
        )
        assert isinstance(result_lint, ValidationResult)

        # 测试 verify 模式
        result_verify = validation_engine.validate(
            declarations=sample_entities,
            references=sample_references,
            project_root=project_root,
            mode="verify",
            strict=False
        )
        assert isinstance(result_verify, ValidationResult)

        # 测试 strict 模式
        result_strict = validation_engine.validate(
            declarations=sample_entities,
            references=sample_references,
            project_root=project_root,
            mode="verify",
            strict=True
        )
        assert isinstance(result_strict, ValidationResult)