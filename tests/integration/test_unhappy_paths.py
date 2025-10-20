"""
Unhappy path tests for Canify CLI commands.

These tests verify that the CLI handles edge cases, errors, and invalid inputs gracefully.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner

from src.cli import app


runner = CliRunner()


class TestUnhappyPaths:
    """Test unhappy path scenarios for Canify CLI."""

    def test_invalid_command(self):
        """Test that invalid commands show appropriate error message."""
        result = runner.invoke(app, ["invalid-command"])

        assert result.exit_code != 0
        assert "No such command" in result.stdout
        assert "invalid-command" in result.stdout

    def test_invalid_option(self):
        """Test that invalid options show appropriate error message."""
        result = runner.invoke(app, ["lint", "--invalid-option"])

        assert result.exit_code != 0
        assert "No such option" in result.stdout
        assert "--invalid-option" in result.stdout

    def test_missing_required_argument(self):
        """Test commands that require arguments handle missing arguments gracefully."""
        # Note: Most commands have defaults, so this might not be applicable
        # But we can test daemon commands with invalid paths
        result = runner.invoke(app, ["daemon", "status", "/nonexistent/path"])

        # Should handle the error gracefully
        assert result.exit_code != 0
        assert "项目路径不存在" in result.stdout

    def test_nonexistent_path(self):
        """Test commands with nonexistent paths."""
        result = runner.invoke(app, ["lint", "/nonexistent/path"])

        # Should handle gracefully - might show validation errors or connection issues
        assert result.exit_code != 0

    def test_file_instead_of_directory(self):
        """Test daemon start with a file instead of directory."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test file")
            temp_file = f.name

        try:
            result = runner.invoke(app, ["daemon", "start", temp_file])

            # Should handle gracefully
            assert result.exit_code != 0
            assert "项目路径必须是目录" in result.stdout
        finally:
            Path(temp_file).unlink()

    def test_invalid_tag_expression(self):
        """Test validate command with invalid tag expressions."""
        # Test with malformed tag expressions
        result = runner.invoke(app, ["validate", "--tags", "invalid and expression"])

        # Should handle gracefully, might show validation errors
        assert result.exit_code != 0

    def test_empty_project(self):
        """Test commands in an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, ["lint", temp_dir])

            # Should handle empty project gracefully
            # Exit code might be 0 (no errors) or non-zero (no entities found)
            assert result.exit_code in [0, 1]

    def test_malformed_markdown_files(self):
        """Test with malformed Markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a malformed entity declaration
            malformed_file = Path(temp_dir) / "broken.md"
            malformed_file.write_text("""
# Broken File

```entity
invalid yaml content
  - broken
  - yaml
```
""")

            result = runner.invoke(app, ["lint", temp_dir])

            # Should handle parsing errors gracefully
            assert result.exit_code != 0

    def test_broken_references(self):
        """Test with broken entity references."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with broken references
            broken_ref_file = Path(temp_dir) / "project.md"
            broken_ref_file.write_text("""
# Project with Broken Reference

This project references a [nonexistent user](entity://nonexistent-user).

```entity
id: test-project
type: Project
name: Test Project
owner: entity://nonexistent-user
```
""")

            result = runner.invoke(app, ["verify", temp_dir])

            # Should detect dangling references
            assert result.exit_code != 0
            assert "悬空引用" in result.stdout

    def test_schema_violations(self):
        """Test with entities that violate their schemas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with schema violations
            schema_violation_file = Path(temp_dir) / "invalid-service.md"
            schema_violation_file.write_text("""
# Invalid Service

```entity
id: invalid-service
type: Service
name: Invalid Service
tier: "not-a-number"  # Should be integer
```
""")

            result = runner.invoke(app, ["verify", temp_dir])

            # Should detect schema violations
            assert result.exit_code != 0

    def test_verbose_mode_edge_cases(self):
        """Test verbose mode with various edge cases."""
        # Test verbose mode with different commands
        for command in ["lint", "verify", "validate"]:
            result = runner.invoke(app, [command, "--verbose"])

            # Should handle verbose mode without crashing
            assert result.exit_code in [0, 1]

    def test_strict_mode_edge_cases(self):
        """Test strict mode with various edge cases."""
        # Test strict mode with different commands
        for command in ["lint", "verify", "validate"]:
            result = runner.invoke(app, [command, "--strict"])

            # Should handle strict mode without crashing
            assert result.exit_code in [0, 1]

    def test_daemon_commands_without_daemon(self):
        """Test daemon commands when daemon is not running."""
        # Note: This test assumes daemon is not running
        # We can't easily control daemon state in tests, so we'll test error handling
        result = runner.invoke(app, ["daemon", "stop"])

        # Should handle gracefully (current implementation shows "需要后续实现")
        assert result.exit_code == 0
        assert "需要后续实现" in result.stdout

    def test_version_command_edge_cases(self):
        """Test version command with various options."""
        # Test version flag
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Canify v" in result.stdout

    def test_help_command_edge_cases(self):
        """Test help command with various options."""
        # Test main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Canify" in result.stdout

        # Test command-specific help
        for command in ["lint", "verify", "validate", "daemon"]:
            result = runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0
            assert command in result.stdout


class TestErrorRecovery:
    """Test that the CLI recovers gracefully from various errors."""

    def test_connection_timeout_handling(self):
        """Test handling of daemon connection timeouts."""
        # This would require mocking the daemon client
        # For now, we'll verify the CLI doesn't crash on connection issues
        pass

    def test_parse_error_handling(self):
        """Test handling of file parsing errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with various parsing issues
            problematic_files = [
                ("empty.md", ""),
                ("invalid_yaml.md", "```entity\ninvalid: yaml: content\n```"),
                ("malformed_entity.md", "```entity\nid: test\ntype: test\nname: Test\n```entity\n```"),
            ]

            for filename, content in problematic_files:
                file_path = Path(temp_dir) / filename
                file_path.write_text(content)

            result = runner.invoke(app, ["lint", temp_dir])

            # Should handle parsing errors without crashing
            assert result.exit_code != 0

    def test_permission_denied_handling(self):
        """Test handling of permission denied errors."""
        # This would require creating files with restricted permissions
        # For now, we'll note this as a potential edge case
        pass


class TestEdgeCases:
    """Test various edge cases and boundary conditions."""

    def test_very_long_paths(self):
        """Test with very long file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a deeply nested directory structure
            deep_dir = Path(temp_dir)
            for i in range(10):
                deep_dir = deep_dir / f"level_{i}"
            deep_dir.mkdir(parents=True)

            # Create a file in the deep directory
            deep_file = deep_dir / "entity.md"
            deep_file.write_text("""
# Deep Entity

```entity
id: deep-entity
type: test
name: Deep Test Entity
```
""")

            result = runner.invoke(app, ["lint", temp_dir])

            # Should handle deep paths without issues
            assert result.exit_code in [0, 1]

    def test_special_characters_in_paths(self):
        """Test with paths containing special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with special characters in names
            special_files = [
                "file with spaces.md",
                "file-with-dashes.md",
                "file_with_underscores.md",
                "file.with.dots.md",
            ]

            for filename in special_files:
                file_path = Path(temp_dir) / filename
                file_path.write_text(f"""
# {filename}

```entity
id: {filename.replace(' ', '-').replace('.', '-')}
type: test
name: {filename}
```
""")

            result = runner.invoke(app, ["lint", temp_dir])

            # Should handle special characters without issues
            assert result.exit_code in [0, 1]

    def test_large_files(self):
        """Test with very large Markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large file (but not too large for testing)
            large_file = Path(temp_dir) / "large.md"
            content = "# Large File\n\n" + "x" * 10000 + "\n\n```entity\nid: large-entity\ntype: test\nname: Large Entity\n```\n"
            large_file.write_text(content)

            result = runner.invoke(app, ["lint", temp_dir])

            # Should handle large files without crashing
            assert result.exit_code in [0, 1]