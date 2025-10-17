#!/usr/bin/env python3
"""
Canify CLI

下一代知识密集型项目的协作基石，将文档即代码的理念推广到所有行业

CLI 作为纯门面函数，所有命令逻辑在独立的命令模块中实现。
"""

import sys

import typer

from .commands import (
    lint as lint_command, 
    version as version_command, 
    verify as verify_command,
    validate as validate_command
)

app = typer.Typer(
    name="canify",
    help="下一代知识密集型项目的协作基石，将文档即代码的理念推广到所有行业",
    no_args_is_help=True,
)


@app.command()
def lint(
    path: str = typer.Argument(
        ".",
        help="要检查的文件或目录路径，默认为当前目录"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="显示详细信息"
    )
):
    """
    检查 Markdown 文件，运行快速的风格和语义检查。
    """
    exit_code = lint_command.run_lint(path, verbose)
    sys.exit(exit_code)


@app.command()
def version():
    """显示 Canify 版本信息"""
    exit_code = version_command.run_version()
    sys.exit(exit_code)


@app.command()
def verify(
    path: str = typer.Argument(
        ".",
        help="要验证的文件或目录路径，默认为当前目录"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="显示详细信息"
    ),
    strict: bool = typer.Option(
        False, "--strict", "-s",
        help="严格模式，将警告视为错误"
    )
):
    """
    执行标准验证，确保核心数据模型的正确性和一致性。
    """
    exit_code = verify_command.run_verify(path, verbose, strict)
    sys.exit(exit_code)


@app.command()
def validate(
    path: str = typer.Argument(
        ".",
        help="要验证的文件或目录路径，默认为当前目录"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="显示详细信息"
    ),
    strict: bool = typer.Option(
        False, "--strict", "-s",
        help="严格模式，将警告视为错误"
    )
):
    """
    执行最严格的深度验证，包含所有业务规则。
    """
    exit_code = validate_command.run_validate(path, verbose, strict)
    sys.exit(exit_code)


if __name__ == "__main__":
    app()