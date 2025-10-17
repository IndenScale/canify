"""
实体引用解析器测试
"""

import pytest
from pathlib import Path

from src.core.parsers import EntityReferenceParser


class TestEntityReferenceParser:
    """实体引用解析器测试类"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return EntityReferenceParser()

    @pytest.fixture
    def test_file_path(self):
        """测试文件路径"""
        return Path("tests/fixtures/test_document.md")

    def test_parse_valid_references(self, parser, test_file_path):
        """测试解析有效的实体引用"""
        # 读取测试文件内容
        content = test_file_path.read_text(encoding="utf-8")

        # 解析实体引用
        references = parser.parse(content, test_file_path)

        # 验证解析结果
        assert len(references) == 5

        # 验证用户引用
        user_references = [r for r in references if r.entity_id in ["user-alice", "user-bob", "user-charlie"]]
        assert len(user_references) == 3

        # 验证任务引用
        task_references = [r for r in references if r.entity_id in ["task-001", "task-002"]]
        assert len(task_references) == 2

        # 验证具体引用内容
        alice_ref = next(r for r in references if r.entity_id == "user-alice")
        assert alice_ref.context_text == "Alice"
        assert alice_ref.reference_type == "link"

        task_001_ref = next(r for r in references if r.entity_id == "task-001")
        assert task_001_ref.context_text == "需求分析"
        assert task_001_ref.reference_type == "link"

    def test_parse_empty_content(self, parser, test_file_path):
        """测试解析空内容"""
        references = parser.parse("", test_file_path)
        assert len(references) == 0

    def test_parse_no_references(self, parser, test_file_path):
        """测试解析没有引用的内容"""
        content = """
# 普通文档

这是一个没有实体引用的文档。

只有普通的Markdown内容。
"""
        references = parser.parse(content, test_file_path)
        assert len(references) == 0

    def test_parse_invalid_references(self, parser, test_file_path):
        """测试解析无效的实体引用"""
        content = """
[无效引用](entity://)  # 缺少ID
[无效引用](entity:// )  # 空白ID
[无效引用](entity://user-with spaces)  # 包含空格
"""
        references = parser.parse(content, test_file_path)
        # 应该跳过无效的引用
        assert len(references) == 0

    def test_location_calculation(self, parser, test_file_path):
        """测试位置信息计算"""
        content = """
第一行
第二行
第三行 [测试引用](entity://test-entity) 第四行
第五行
"""
        references = parser.parse(content, test_file_path)
        assert len(references) == 1

        reference = references[0]
        assert reference.location.start_line == 4  # 引用所在行
        assert reference.location.end_line == 4    # 引用所在行
        assert reference.location.file_path == test_file_path

    def test_multiple_references(self, parser, test_file_path):
        """测试解析多个引用"""
        content = """
[引用1](entity://entity-1) 中间内容 [引用2](entity://entity-2)

[引用3](entity://entity-3) 在另一行
"""
        references = parser.parse(content, test_file_path)
        assert len(references) == 3

        # 验证所有引用都被正确解析
        entity_ids = [r.entity_id for r in references]
        assert "entity-1" in entity_ids
        assert "entity-2" in entity_ids
        assert "entity-3" in entity_ids

    def test_reference_with_special_characters(self, parser, test_file_path):
        """测试解析包含特殊字符的引用"""
        content = """
[包含-连字符](entity://entity-with-dashes)
[包含_下划线](entity://entity_with_underscores)
[包含.点](entity://entity.with.dots)
[包含数字123](entity://entity123)
"""
        references = parser.parse(content, test_file_path)
        assert len(references) == 4

        # 验证特殊字符被正确处理
        entity_ids = [r.entity_id for r in references]
        assert "entity-with-dashes" in entity_ids
        assert "entity_with_underscores" in entity_ids
        assert "entity.with.dots" in entity_ids
        assert "entity123" in entity_ids

    def test_reference_context_text(self, parser, test_file_path):
        """测试引用上下文文本"""
        content = """
[简单引用](entity://simple)
[带空格的引用](entity://with-spaces)
[包含特殊字符的引用!@#$%](entity://special-chars)
[中文引用](entity://chinese)
"""
        references = parser.parse(content, test_file_path)
        assert len(references) == 4

        # 验证上下文文本
        context_texts = [r.context_text for r in references]
        assert "简单引用" in context_texts
        assert "带空格的引用" in context_texts
        assert "包含特殊字符的引用!@#$%" in context_texts
        assert "中文引用" in context_texts