"""
CLI 命令集成测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.commands import lint, verify, validate
from src.core.models import ValidationResult


class TestCLICommands:
    """CLI 命令集成测试类"""

    @pytest.fixture
    def temp_markdown_file(self):
        """创建临时 Markdown 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""
# 测试文档

这是一个包含实体声明和引用的测试文档。

## 项目信息

本项目由 [Alice](entity://user-alice) 负责管理。

## 附录：实体定义

```entity
type: project
id: test-project
name: 测试项目
budget: 10000.0
status: active
```

```entity
type: user
id: user-alice
name: Alice Zhang
email: alice@example.com
```
""")
            temp_path = f.name

        yield Path(temp_path)

        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_directory_with_markdown(self):
        """创建包含 Markdown 文件的临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建多个 Markdown 文件
            files = [
                ("project.md", """
# 项目文档

```entity
type: project
id: test-project
name: 测试项目
budget: 10000.0
status: active
```
"""),
                ("users.md", """
# 用户文档

```entity
type: user
id: user-alice
name: Alice Zhang
email: alice@example.com
```

```entity
type: user
id: user-bob
name: Bob Li
email: bob@example.com
```
"""),
                ("tasks.md", """
# 任务文档

```entity
type: task
id: task-001
name: 需求分析
project_id: test-project
assignee: user-alice
status: in-progress
```
""")
            ]

            for filename, content in files:
                file_path = temp_path / filename
                file_path.write_text(content, encoding='utf-8')

            yield temp_path

    def test_lint_command_with_valid_file(self, temp_markdown_file):
        """测试 lint 命令处理有效文件"""
        with patch('src.commands.lint.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 0

            exit_code = lint.run_lint(str(temp_markdown_file), verbose=False)

            assert exit_code == 0
            mock_pipeline.assert_called_once_with(
                str(temp_markdown_file),
                False,  # verbose
                mode="lint",
                strict=False
            )

    def test_lint_command_with_verbose(self, temp_markdown_file):
        """测试 lint 命令的详细模式"""
        with patch('src.commands.lint.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 0

            exit_code = lint.run_lint(str(temp_markdown_file), verbose=True)

            assert exit_code == 0
            mock_pipeline.assert_called_once_with(
                str(temp_markdown_file),
                True,  # verbose
                mode="lint",
                strict=False
            )

    def test_verify_command_with_valid_directory(self, temp_directory_with_markdown):
        """测试 verify 命令处理有效目录"""
        with patch('src.commands.verify.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 0

            exit_code = verify.run_verify(str(temp_directory_with_markdown), verbose=False, strict=False)

            assert exit_code == 0
            mock_pipeline.assert_called_once_with(
                str(temp_directory_with_markdown),
                False,  # verbose
                mode="verify",
                strict=False
            )

    def test_verify_command_with_strict_mode(self, temp_directory_with_markdown):
        """测试 verify 命令的严格模式"""
        with patch('src.commands.verify.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 0

            exit_code = verify.run_verify(str(temp_directory_with_markdown), verbose=False, strict=True)

            assert exit_code == 0
            mock_pipeline.assert_called_once_with(
                str(temp_directory_with_markdown),
                False,  # verbose
                mode="verify",
                strict=True
            )

    def test_validate_command(self, temp_directory_with_markdown):
        """测试 validate 命令"""
        with patch('src.commands.validate.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 0

            exit_code = validate.run_validate(str(temp_directory_with_markdown), verbose=False, strict=False)

            assert exit_code == 0
            mock_pipeline.assert_called_once_with(
                str(temp_directory_with_markdown),
                False,  # verbose
                mode="validate",
                strict=False
            )

    def test_lint_command_with_nonexistent_path(self):
        """测试 lint 命令处理不存在的路径"""
        with patch('src.commands.lint.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 1

            exit_code = lint.run_lint("/nonexistent/path", verbose=False)

            assert exit_code == 1

    def test_verify_command_with_validation_errors(self, temp_directory_with_markdown):
        """测试 verify 命令处理验证错误"""
        with patch('src.commands.verify.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 1  # 模拟验证失败

            exit_code = verify.run_verify(str(temp_directory_with_markdown), verbose=False, strict=False)

            assert exit_code == 1

    def test_commands_with_empty_directory(self):
        """测试命令处理空目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.commands.lint.run_validation_pipeline') as mock_lint_pipeline, \
                 patch('src.commands.verify.run_validation_pipeline') as mock_verify_pipeline, \
                 patch('src.commands.validate.run_validation_pipeline') as mock_validate_pipeline:

                mock_lint_pipeline.return_value = 0
                mock_verify_pipeline.return_value = 0
                mock_validate_pipeline.return_value = 0

                # 测试 lint
                exit_code = lint.run_lint(temp_dir, verbose=False)
                assert exit_code == 0

                # 测试 verify
                exit_code = verify.run_verify(temp_dir, verbose=False, strict=False)
                assert exit_code == 0

                # 测试 validate
                exit_code = validate.run_validate(temp_dir, verbose=False, strict=False)
                assert exit_code == 0

    def test_commands_with_current_directory(self):
        """测试命令处理当前目录"""
        with patch('src.commands.lint.run_validation_pipeline') as mock_lint_pipeline, \
             patch('src.commands.verify.run_validation_pipeline') as mock_verify_pipeline, \
             patch('src.commands.validate.run_validation_pipeline') as mock_validate_pipeline:

            mock_lint_pipeline.return_value = 0
            mock_verify_pipeline.return_value = 0
            mock_validate_pipeline.return_value = 0

            # 测试默认路径（当前目录）
            exit_code = lint.run_lint(".", verbose=False)
            assert exit_code == 0

            exit_code = verify.run_verify(".", verbose=False, strict=False)
            assert exit_code == 0

            exit_code = validate.run_validate(".", verbose=False, strict=False)
            assert exit_code == 0

    def test_commands_error_handling(self):
        """测试命令错误处理"""
        with patch('src.commands.lint.run_validation_pipeline') as mock_pipeline:
            # 模拟验证失败情况
            mock_pipeline.return_value = 1

            # 应该返回错误代码 1
            exit_code = lint.run_lint(".", verbose=False)
            assert exit_code == 1

    def test_verbose_output_formatting(self, temp_markdown_file):
        """测试详细输出格式"""
        with patch('src.commands.lint.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 0

            # 测试详细模式
            exit_code = lint.run_lint(str(temp_markdown_file), verbose=True)
            assert exit_code == 0

            # 验证调用了详细模式
            mock_pipeline.assert_called_with(
                str(temp_markdown_file),
                True,  # verbose
                mode="lint",
                strict=False
            )

    def test_strict_mode_behavior(self, temp_directory_with_markdown):
        """测试严格模式行为"""
        with patch('src.commands.verify.run_validation_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 0

            # 测试严格模式
            exit_code = verify.run_verify(str(temp_directory_with_markdown), verbose=False, strict=True)
            assert exit_code == 0

            # 验证调用了严格模式
            mock_pipeline.assert_called_with(
                str(temp_directory_with_markdown),
                False,  # verbose
                mode="verify",
                strict=True
            )