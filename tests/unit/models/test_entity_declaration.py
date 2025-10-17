"""
实体声明模型测试
"""

import pytest
from pathlib import Path

from src.core.models import EntityDeclaration, Location


class TestEntityDeclaration:
    """实体声明模型测试类"""

    def test_create_entity_declaration(self):
        """测试创建实体声明"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        entity = EntityDeclaration(
            location=location,
            entity_type="project",
            entity_id="test-project",
            name="测试项目",
            raw_data={
                "type": "project",
                "id": "test-project",
                "name": "测试项目",
                "budget": 10000.0,
                "status": "active"
            },
            source_code="type: project\nid: test-project\nname: 测试项目\nbudget: 10000.0\nstatus: active"
        )

        assert entity.entity_type == "project"
        assert entity.entity_id == "test-project"
        assert entity.name == "测试项目"
        assert entity.raw_data["budget"] == 10000.0
        assert entity.raw_data["status"] == "active"
        assert entity.location == location

    def test_entity_string_representation(self):
        """测试实体字符串表示"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        entity = EntityDeclaration(
            location=location,
            entity_type="task",
            entity_id="task-001",
            name="需求分析",
            raw_data={
                "type": "task",
                "id": "task-001",
                "name": "需求分析",
                "status": "completed"
            },
            source_code="type: task\nid: task-001\nname: 需求分析\nstatus: completed"
        )

        assert str(entity) == "task::task-001 (需求分析)"

    def test_entity_with_complex_data(self):
        """测试包含复杂数据的实体"""
        location = Location(
            file_path=Path("test.md"),
            start_line=20,
            end_line=25
        )

        raw_data = {
            "type": "project",
            "id": "complex-project",
            "name": "复杂项目",
            "budget": 50000.0,
            "status": "active",
            "tags": ["important", "urgent"],
            "metadata": {
                "priority": "high",
                "deadline": "2025-12-31"
            }
        }

        entity = EntityDeclaration(
            location=location,
            entity_type="project",
            entity_id="complex-project",
            name="复杂项目",
            raw_data=raw_data,
            source_code=str(raw_data)
        )

        assert entity.entity_type == "project"
        assert entity.entity_id == "complex-project"
        assert entity.raw_data["tags"] == ["important", "urgent"]
        assert entity.raw_data["metadata"]["priority"] == "high"

    def test_entity_validation_with_empty_name(self):
        """测试空名称字段的实体验证"""
        location = Location(
            file_path=Path("test.md"),
            start_line=10,
            end_line=15
        )

        # 空字符串作为名称 - Pydantic 允许空字符串
        entity = EntityDeclaration(
            location=location,
            entity_type="project",
            entity_id="test-project",
            name="",  # 空字符串
            raw_data={
                "type": "project",
                "id": "test-project",
                "name": ""  # 空字符串
            },
            source_code="type: project\nid: test-project\nname: "
        )

        assert entity.name == ""  # 应该允许空字符串