"""
实体声明解析器测试
"""

import pytest
from pathlib import Path

from src.core.parsers import EntityDeclarationParser


class TestEntityDeclarationParser:
    """实体声明解析器测试类"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return EntityDeclarationParser()

    @pytest.fixture
    def test_file_path(self):
        """测试文件路径"""
        return Path("tests/fixtures/test_document.md")

    def test_parse_valid_entities(self, parser, test_file_path):
        """测试解析有效的实体声明"""
        # 读取测试文件内容
        content = test_file_path.read_text(encoding="utf-8")

        # 解析实体声明
        declarations = parser.parse(content, test_file_path)

        # 验证解析结果
        assert len(declarations) == 5

        # 验证项目实体
        project_entity = next(d for d in declarations if d.entity_id == "test-project")
        assert project_entity.entity_type == "project"
        assert project_entity.name == "测试项目"
        assert project_entity.raw_data["budget"] == 10000.0
        assert project_entity.raw_data["status"] == "active"

        # 验证用户实体
        user_entities = [d for d in declarations if d.entity_type == "user"]
        assert len(user_entities) == 2

        alice_entity = next(d for d in user_entities if d.entity_id == "user-alice")
        assert alice_entity.name == "Alice Zhang"
        assert alice_entity.raw_data["email"] == "alice@example.com"

        # 验证任务实体
        task_entities = [d for d in declarations if d.entity_type == "task"]
        assert len(task_entities) == 2

        task_001 = next(d for d in task_entities if d.entity_id == "task-001")
        assert task_001.name == "需求分析"
        assert task_001.raw_data["status"] == "completed"

    def test_parse_empty_content(self, parser, test_file_path):
        """测试解析空内容"""
        declarations = parser.parse("", test_file_path)
        assert len(declarations) == 0

    def test_parse_no_entities(self, parser, test_file_path):
        """测试解析没有实体的内容"""
        content = """
# 普通文档

这是一个没有实体声明的文档。

只有普通的Markdown内容。
"""
        declarations = parser.parse(content, test_file_path)
        assert len(declarations) == 0

    def test_parse_invalid_yaml(self, parser, test_file_path):
        """测试解析无效的YAML内容"""
        content = """
```entity
invalid yaml content: [
  missing closing bracket
```
"""
        declarations = parser.parse(content, test_file_path)
        # 应该跳过无效的实体声明
        assert len(declarations) == 0

    def test_parse_missing_required_fields(self, parser, test_file_path):
        """测试解析缺少必需字段的实体"""
        content = """
```entity
name: 测试实体
# 缺少 type 和 id 字段
```
"""
        declarations = parser.parse(content, test_file_path)
        # 应该跳过缺少必需字段的实体
        assert len(declarations) == 0

    def test_location_calculation(self, parser, test_file_path):
        """测试位置信息计算"""
        content = """
第一行
第二行
第三行
```entity
type: test
type: test
id: test-entity
name: 测试实体
```
第五行
"""
        declarations = parser.parse(content, test_file_path)
        assert len(declarations) == 1

        entity = declarations[0]
        assert entity.location.start_line == 5  # ```entity 所在行
        assert entity.location.end_line == 10   # ``` 所在行
        assert entity.location.file_path == test_file_path

    def test_multiple_entities(self, parser, test_file_path):
        """测试解析多个实体"""
        content = """
```entity
type: user
id: user-1
name: 用户1
```

中间内容

```entity
type: user
id: user-2
name: 用户2
```
"""
        declarations = parser.parse(content, test_file_path)
        assert len(declarations) == 2

        # 验证两个实体都被正确解析
        entity_ids = [d.entity_id for d in declarations]
        assert "user-1" in entity_ids
        assert "user-2" in entity_ids

    def test_entity_with_complex_data(self, parser, test_file_path):
        """测试解析包含复杂数据的实体"""
        content = """
```entity
type: project
id: complex-project
name: 复杂项目
budget: 50000.0
status: active
tags:
  - important
  - urgent
metadata:
  priority: high
  deadline: "2025-12-31"
```
"""
        declarations = parser.parse(content, test_file_path)
        assert len(declarations) == 1

        entity = declarations[0]
        assert entity.entity_type == "project"
        assert entity.entity_id == "complex-project"
        assert entity.raw_data["budget"] == 50000.0
        assert entity.raw_data["tags"] == ["important", "urgent"]
        assert entity.raw_data["metadata"]["priority"] == "high"