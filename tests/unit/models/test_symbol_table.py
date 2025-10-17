"""
符号表模型测试
"""

import pytest
from pathlib import Path

from src.core.models import SymbolTable, EntityDeclaration, EntityReference, Location


class TestSymbolTable:
    """符号表模型测试类"""

    @pytest.fixture
    def symbol_table(self):
        """创建符号表实例"""
        return SymbolTable()

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
                    "budget": 10000.0
                },
                source_code="type: project\nid: test-project\nname: 测试项目\nbudget: 10000.0"
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

    def test_add_and_find_entity(self, symbol_table, sample_entities):
        """测试添加和查找实体"""
        # 添加实体
        for entity in sample_entities:
            symbol_table.add_entity(entity)

        # 验证实体总数
        assert symbol_table.total_entities == 3

        # 查找存在的实体
        found_entity = symbol_table.find_entity("user-alice")
        assert found_entity is not None
        assert found_entity.entity_id == "user-alice"
        assert found_entity.name == "Alice Zhang"

        # 查找不存在的实体
        not_found_entity = symbol_table.find_entity("non-existent")
        assert not_found_entity is None

    def test_add_and_get_references(self, symbol_table, sample_references):
        """测试添加和获取引用"""
        # 添加引用
        for reference in sample_references:
            symbol_table.add_reference(reference)

        # 验证引用总数
        assert symbol_table.total_references == 3

        # 获取指向特定实体的引用
        alice_references = symbol_table.get_references_to("user-alice")
        assert len(alice_references) == 1
        assert alice_references[0].entity_id == "user-alice"
        assert alice_references[0].context_text == "Alice"

        # 获取指向不存在的实体的引用
        non_existent_references = symbol_table.get_references_to("non-existent")
        assert len(non_existent_references) == 0

    def test_get_entities_by_type(self, symbol_table, sample_entities):
        """测试按类型获取实体"""
        # 添加实体
        for entity in sample_entities:
            symbol_table.add_entity(entity)

        # 获取项目类型实体
        project_entities = symbol_table.get_entities_by_type("project")
        assert len(project_entities) == 1
        assert project_entities[0].entity_id == "test-project"

        # 获取用户类型实体
        user_entities = symbol_table.get_entities_by_type("user")
        assert len(user_entities) == 2
        user_ids = [entity.entity_id for entity in user_entities]
        assert "user-alice" in user_ids
        assert "user-bob" in user_ids

        # 获取不存在的类型实体
        task_entities = symbol_table.get_entities_by_type("task")
        assert len(task_entities) == 0

    def test_entity_type_grouping(self, symbol_table, sample_entities):
        """测试实体类型分组"""
        # 添加实体
        for entity in sample_entities:
            symbol_table.add_entity(entity)

        # 验证类型分组
        assert "project" in symbol_table.entity_types
        assert "user" in symbol_table.entity_types
        assert len(symbol_table.entity_types["project"]) == 1
        assert len(symbol_table.entity_types["user"]) == 2

    def test_empty_symbol_table(self, symbol_table):
        """测试空符号表"""
        assert symbol_table.total_entities == 0
        assert symbol_table.total_references == 0
        assert len(symbol_table.entity_types) == 0

        # 在空符号表中查找
        assert symbol_table.find_entity("any") is None
        assert len(symbol_table.get_references_to("any")) == 0
        assert len(symbol_table.get_entities_by_type("any")) == 0

    def test_duplicate_entity_id(self, symbol_table, sample_entities):
        """测试重复实体ID的处理"""
        # 添加第一个实体
        symbol_table.add_entity(sample_entities[0])

        # 尝试添加相同ID的实体（应该覆盖）
        duplicate_entity = EntityDeclaration(
            location=sample_entities[0].location,
            entity_type="user",  # 不同类型
            entity_id="test-project",  # 相同ID
            name="重复项目",
            raw_data={
                "type": "user",
                "id": "test-project",
                "name": "重复项目"
            },
            source_code="type: user\nid: test-project\nname: 重复项目"
        )

        symbol_table.add_entity(duplicate_entity)

        # 验证最后一个添加的实体被保留
        assert symbol_table.total_entities == 1
        found_entity = symbol_table.find_entity("test-project")
        assert found_entity.entity_type == "user"
        assert found_entity.name == "重复项目"

    def test_reference_management(self, symbol_table, sample_entities, sample_references):
        """测试引用管理"""
        # 添加实体和引用
        for entity in sample_entities:
            symbol_table.add_entity(entity)

        for reference in sample_references:
            symbol_table.add_reference(reference)

        # 验证引用指向的实体存在
        for reference in sample_references:
            entity = symbol_table.find_entity(reference.entity_id)
            assert entity is not None, f"引用指向的实体 {reference.entity_id} 不存在"