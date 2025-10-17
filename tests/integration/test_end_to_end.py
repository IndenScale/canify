"""
端到端测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.commands.utils import run_validation_pipeline
from src.core.validation_engine import ValidationEngine
from src.core.parsers import EntityDeclarationParser, EntityReferenceParser


class TestEndToEnd:
    """端到端测试类"""

    @pytest.fixture
    def valid_project_structure(self):
        """创建有效的项目结构"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建项目结构
            (temp_path / "entities").mkdir()
            (temp_path / "entities" / "projects").mkdir()
            (temp_path / "entities" / "users").mkdir()
            (temp_path / "entities" / "tasks").mkdir()

            # 创建项目文件
            project_file = temp_path / "entities" / "projects" / "canify.md"
            project_file.write_text("""
# Canify 项目

```entity
type: project
id: canify-development
name: Canify 开发项目
budget: 50000.0
status: active
manager: user-alice
developers: ["user-alice", "user-bob", "user-eve"]
```
""", encoding='utf-8')

            # 创建用户文件
            users_file = temp_path / "entities" / "users" / "team.md"
            users_file.write_text("""
# 团队成员

```entity
type: user
id: user-alice
name: Alice Zhang
email: alice@example.com
role: project-manager
```

```entity
type: user
id: user-bob
name: Bob Li
email: bob@example.com
role: developer
```

```entity
type: user
id: user-eve
name: Eve Wang
email: eve@example.com
role: product-manager
```
""", encoding='utf-8')

            # 创建任务文件
            tasks_file = temp_path / "entities" / "tasks" / "backlog.md"
            tasks_file.write_text("""
# 任务列表

```entity
type: task
id: task-001
name: 需求分析
project_id: canify-development
assignee: user-alice
estimated_hours: 40.0
actual_hours: 35.5
status: completed
```

```entity
type: task
id: task-002
name: 架构设计
project_id: canify-development
assignee: user-bob
estimated_hours: 60.0
actual_hours: TBD
status: in-progress
```

```entity
type: task
id: task-003
name: 产品规划
project_id: canify-development
assignee: user-eve
estimated_hours: 30.0
actual_hours: TBD
status: in-progress
```
""", encoding='utf-8')

            # 创建主文档文件
            main_doc = temp_path / "README.md"
            main_doc.write_text("""
# Canify 项目文档

## 项目概述

本项目由 [Alice Zhang](entity://user-alice) 负责管理，技术架构由 [Bob Li](entity://user-bob) 设计，产品规划由 [Eve Wang](entity://user-eve) 负责。

## 当前任务

- [需求分析](entity://task-001) - 已完成
- [架构设计](entity://task-002) - 进行中
- [产品规划](entity://task-003) - 进行中

## 项目状态

当前项目 [Canify 开发项目](entity://canify-development) 处于活跃状态。
""", encoding='utf-8')

            yield temp_path

    @pytest.fixture
    def invalid_project_structure(self):
        """创建包含错误的项目结构"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建包含错误的项目结构
            (temp_path / "entities").mkdir()

            # 创建包含重复ID的文件
            duplicate_file = temp_path / "entities" / "duplicate.md"
            duplicate_file.write_text("""
```entity
type: project
id: duplicate-id
name: 项目1
```

```entity
type: task
id: duplicate-id
name: 任务1
```
""", encoding='utf-8')

            # 创建包含悬空引用的文件
            dangling_file = temp_path / "entities" / "dangling.md"
            dangling_file.write_text("""
# 悬空引用测试

[不存在的实体](entity://non-existent-entity)

```entity
type: user
id: user-test
name: 测试用户
```
""", encoding='utf-8')

            # 创建包含类型错误的文件
            type_error_file = temp_path / "entities" / "type_errors.md"
            type_error_file.write_text("""
```entity
type: project
id: type-error-project
name: 类型错误项目
budget: "not-a-number"
status: "invalid-status"
developers: "not-a-list"
```
""", encoding='utf-8')

            yield temp_path

    def test_valid_project_validation(self, valid_project_structure):
        """测试有效项目的验证"""
        # 使用验证管道
        exit_code = run_validation_pipeline(
            path=str(valid_project_structure),
            verbose=False,
            mode="verify",
            strict=False
        )

        assert exit_code == 0

    def test_invalid_project_validation(self, invalid_project_structure):
        """测试无效项目的验证"""
        # 使用验证管道
        exit_code = run_validation_pipeline(
            path=str(invalid_project_structure),
            verbose=False,
            mode="verify",
            strict=False
        )

        # 应该检测到错误
        assert exit_code == 1

    def test_validation_engine_integration(self, valid_project_structure):
        """测试验证引擎集成"""
        # 手动解析文件
        parser = EntityDeclarationParser()
        reference_parser = EntityReferenceParser()

        all_declarations = []
        all_references = []

        # 解析所有 Markdown 文件
        for file_path in valid_project_structure.rglob("*.md"):
            content = file_path.read_text(encoding='utf-8')
            declarations = parser.parse(content, file_path)
            references = reference_parser.parse(content, file_path)

            all_declarations.extend(declarations)
            all_references.extend(references)

        # 使用验证引擎
        validation_engine = ValidationEngine()
        result = validation_engine.validate(
            declarations=all_declarations,
            references=all_references,
            project_root=valid_project_structure,
            mode="verify",
            strict=False
        )

        assert result.success is True
        assert len(result.errors) == 0

    def test_strict_mode_validation(self, valid_project_structure):
        """测试严格模式验证"""
        # 使用验证管道
        exit_code = run_validation_pipeline(
            path=str(valid_project_structure),
            verbose=False,
            mode="validate",
            strict=True
        )

        assert exit_code == 0

    def test_lint_mode_performance(self, valid_project_structure):
        """测试 lint 模式性能"""
        import time

        # 测量 lint 模式执行时间
        start_time = time.time()
        exit_code = run_validation_pipeline(
            path=str(valid_project_structure),
            verbose=False,
            mode="lint",
            strict=False
        )
        end_time = time.time()

        execution_time = end_time - start_time

        assert exit_code == 0
        # lint 模式应该很快（小于 1 秒）
        assert execution_time < 1.0

    def test_multiple_validation_modes(self, valid_project_structure):
        """测试多种验证模式"""
        # 测试 lint 模式
        lint_exit_code = run_validation_pipeline(
            path=str(valid_project_structure),
            verbose=False,
            mode="lint",
            strict=False
        )
        assert lint_exit_code == 0

        # 测试 verify 模式
        verify_exit_code = run_validation_pipeline(
            path=str(valid_project_structure),
            verbose=False,
            mode="verify",
            strict=False
        )
        assert verify_exit_code == 0

        # 测试 validate 模式
        validate_exit_code = run_validation_pipeline(
            path=str(valid_project_structure),
            verbose=False,
            mode="validate",
            strict=False
        )
        assert validate_exit_code == 0

    def test_error_recovery_and_continuation(self, invalid_project_structure):
        """测试错误恢复和继续处理"""
        # 即使有错误，验证引擎应该继续处理其他文件
        exit_code = run_validation_pipeline(
            path=str(invalid_project_structure),
            verbose=False,
            mode="verify",
            strict=False
        )

        # 应该检测到错误，但不会崩溃
        assert exit_code == 1

    def test_complex_reference_network(self):
        """测试复杂引用网络"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建复杂的引用网络
            complex_file = temp_path / "complex.md"
            complex_file.write_text("""
# 复杂引用网络测试

## 项目结构

[核心项目](entity://core-project) 由 [项目经理](entity://project-manager) 负责。

## 团队结构

[开发团队](entity://dev-team) 包含 [前端开发](entity://frontend-dev) 和 [后端开发](entity://backend-dev)。

## 任务分配

[前端任务](entity://frontend-task) 分配给 [前端开发](entity://frontend-dev)。
[后端任务](entity://backend-task) 分配给 [后端开发](entity://backend-dev)。

## 实体定义

```entity
type: project
id: core-project
name: 核心项目
manager: project-manager
team: dev-team
```

```entity
type: user
id: project-manager
name: 项目经理
role: manager
```

```entity
type: team
id: dev-team
name: 开发团队
members: [frontend-dev, backend-dev]
```

```entity
type: user
id: frontend-dev
name: 前端开发
role: developer
```

```entity
type: user
id: backend-dev
name: 后端开发
role: developer
```

```entity
type: task
id: frontend-task
name: 前端任务
assignee: frontend-dev
project: core-project
```

```entity
type: task
id: backend-task
name: 后端任务
assignee: backend-dev
project: core-project
```
""", encoding='utf-8')

            # 验证复杂引用网络
            exit_code = run_validation_pipeline(
                path=str(temp_path),
                verbose=False,
                mode="verify",
                strict=False
            )

            assert exit_code == 0