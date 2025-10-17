"""
Canify 命令的共享工具函数和核心执行流水线
"""

from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 使用绝对路径导入，以修复 Pylint E0402
from ..core import (
    BusinessRuleViolation,
    DanglingReferenceError,
    DuplicateEntityIdError,
    EntityDeclaration,
    EntityReference,
    EntityDeclarationParser,
    EntityReferenceParser,
    InvalidFieldValueError,
    MissingRequiredFieldError,
    TypeValidationError,
    ValidationEngine,
    ValidationResult,
)


def find_markdown_files(path: Path) -> List[Path]:
    """查找指定路径下的所有 Markdown 文件"""
    if path.is_file() and path.suffix.lower() == ".md":
        return [path]
    if path.is_dir():
        return list(path.rglob("*.md"))
    return []


def parse_file(file_path: Path) -> tuple[List[EntityDeclaration], List[EntityReference], List[str]]:
    """解析单个文件中的实体声明和引用"""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"无法读取文件 {file_path}: {e}")
        return [], [], errors

    declaration_parser = EntityDeclarationParser()
    reference_parser = EntityReferenceParser()
    declarations = declaration_parser.parse(content, file_path)
    references = reference_parser.parse(content, file_path)
    return declarations, references, errors


def format_error_message(error: Exception) -> str:
    """格式化错误/警告消息用于显示"""
    # ... (实现与之前相同)
    return str(error)


def format_location(error: Exception) -> str:
    """格式化错误/警告的位置"""
    if hasattr(error, 'location') and error.location:
        return f"{error.location.file_path.name}:{error.location.start_line}"
    return "未知位置"


def display_results(result: ValidationResult, console: Console, error_console: Console):
    """显示验证结果"""
    # ... (实现与之前相同)
    error_count = len(result.errors)
    warning_count = len(result.warnings)

    if result.success:
        title = "✅ 验证通过"
        border_style = "green"
        message = f"- {warning_count} 个警告"
    else:
        title = "❌ 验证失败"
        border_style = "red"
        message = f"- {error_count} 个错误\n- {warning_count} 个警告"

    console.print(Panel.fit(f"[bold]{title}[/bold]\n{message}", title="验证结果", border_style=border_style))

    if result.warnings:
        table = Table(title="警告详情", show_header=True, header_style="bold yellow")
        table.add_column("警告类型", style="dim", width=20)
        table.add_column("位置", style="dim", width=25)
        table.add_column("警告描述", style="yellow")
        for warning in result.warnings:
            table.add_row(warning.__class__.__name__, format_location(warning), format_error_message(warning))
        console.print(table)

    if result.errors:
        table = Table(title="错误详情", show_header=True, header_style="bold red")
        table.add_column("错误类型", style="dim", width=20)
        table.add_column("位置", style="dim", width=25)
        table.add_column("错误描述", style="white")
        for error in result.errors:
            table.add_row(error.__class__.__name__, format_location(error), format_error_message(error))
        error_console.print(table)


def run_validation_pipeline(path: str, verbose: bool, mode: str, strict: bool) -> int:
    """所有验证命令共享的核心执行流水线"""
    console = Console()
    error_console = Console(stderr=True)

    try:
        if verbose:
            console.print(f"[blue]在 {mode} 模式下运行...[/blue]")

        target_path = Path(path).resolve()
        if not target_path.exists():
            error_console.print(f"[red]错误: 路径 '{path}' 不存在[/red]")
            return 1

        markdown_files = find_markdown_files(target_path)
        if not markdown_files:
            error_console.print(f"[yellow]警告: 在 '{path}' 中未找到任何 Markdown 文件[/yellow]")
            return 0

        all_declarations, all_references, all_errors = [], [], []
        for file_path in markdown_files:
            declarations, references, errors = parse_file(file_path)
            all_declarations.extend(declarations)
            all_references.extend(references)
            all_errors.extend(errors)

        if all_errors:
            console.print("[red]解析错误:[/red]")
            for error in all_errors:
                console.print(f"  - {error}")
            return 1

        validation_engine = ValidationEngine()
        result = validation_engine.validate(
            declarations=all_declarations,
            references=all_references,
            project_root=target_path,
            mode=mode,
            strict=strict
        )

        display_results(result, console, error_console)

        return 0 if result.success else 1

    except Exception as e:
        error_console.print(f"[red]验证过程中发生意外错误: {e}[/red]")
        return 1