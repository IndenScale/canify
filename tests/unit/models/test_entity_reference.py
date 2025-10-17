"""
实体引用模型测试
"""

import pytest
from pathlib import Path

from src.core.models import EntityReference, Location


class TestEntityReference:
    """实体引用模型测试类"""

    def test_create_entity_reference(self):
        """测试创建实体引用"""
        location = Location(
            file_path=Path("test.md"),
            start_line=5,
            end_line=5
        )

        reference = EntityReference(
            location=location,
            entity_id="user-alice",
            context_text="Alice",
            reference_type="link"
        )

        assert reference.entity_id == "user-alice"
        assert reference.context_text == "Alice"
        assert reference.reference_type == "link"
        assert reference.location == location

    def test_reference_string_representation(self):
        """测试引用字符串表示"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=10
        )

        reference = EntityReference(
            location=location,
            entity_id="task-001",
            context_text="需求分析",
            reference_type="link"
        )

        assert str(reference) == f"引用 task-001 在 {location}"

    def test_reference_with_special_characters(self):
        """测试包含特殊字符的引用"""
        location = Location(
            file_path=Path("test.md"),
            start_line=15,
            end_line=15
        )

        # 测试各种特殊字符
        test_cases = [
            ("entity-with-dashes", "包含-连字符"),
            ("entity_with_underscores", "包含_下划线"),
            ("entity.with.dots", "包含.点"),
            ("entity123", "包含数字123"),
            ("entity-with-multiple-dashes", "包含-多个-连字符"),
            ("entity_with_multiple_underscores", "包含_多个_下划线")
        ]

        for entity_id, context_text in test_cases:
            reference = EntityReference(
                location=location,
                entity_id=entity_id,
                context_text=context_text,
                reference_type="link"
            )

            assert reference.entity_id == entity_id
            assert reference.context_text == context_text

    def test_reference_with_unicode_characters(self):
        """测试包含Unicode字符的引用"""
        location = Location(
            file_path=Path("test.md"),
            start_line=20,
            end_line=20
        )

        # 测试中文和其他Unicode字符
        test_cases = [
            ("user-张三", "张三"),
            ("user-李四", "李四"),
            ("user-王五", "王五"),
            ("task-需求分析", "需求分析"),
            ("task-架构设计", "架构设计")
        ]

        for entity_id, context_text in test_cases:
            reference = EntityReference(
                location=location,
                entity_id=entity_id,
                context_text=context_text,
                reference_type="link"
            )

            assert reference.entity_id == entity_id
            assert reference.context_text == context_text

    def test_reference_default_type(self):
        """测试引用默认类型"""
        location = Location(
            file_path=Path("test.md"),
            start_line=5,
            end_line=5
        )

        # 不指定 reference_type，应该使用默认值
        reference = EntityReference(
            location=location,
            entity_id="user-alice",
            context_text="Alice"
        )

        assert reference.reference_type == "link"

    def test_reference_with_empty_context(self):
        """测试空上下文文本的引用"""
        location = Location(
            file_path=Path("test.md"),
            start_line=5,
            end_line=5
        )

        reference = EntityReference(
            location=location,
            entity_id="user-alice",
            context_text=""  # 空字符串
        )

        assert reference.context_text == ""