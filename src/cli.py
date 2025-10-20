#!/usr/bin/env python3
"""
Canify CLI - 轻量级前端

下一代知识密集型项目的协作基石，将文档即代码的理念推广到所有行业

CLI 作为纯门面函数，所有计算逻辑由 daemon 处理。
"""

import sys
from pathlib import Path
from typing import Optional

import typer

from .client.daemon_client import DaemonClient
from .commands import daemon as daemon_command
from .commands import version as version_command

def version_callback(value: bool):
    if value:
        version_command.run_version()
        raise typer.Exit()

app = typer.Typer(
    name="canify",
    help="下一代知识密集型项目的协作基石，将文档即代码的理念推广到所有行业",
    no_args_is_help=True,
)

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="显示 Canify 版本信息并退出。",
        callback=version_callback,
        is_eager=True,
    )
):
    """
    Canify: 下一代知识密集型项目的协作基石。
    """
    pass


@app.command()
def lint(
    path: str = typer.Argument(
        ".",
        help="要检查的文件或目录路径，默认为当前目录"
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
    检查 Markdown 文件，运行快速的风格和语义检查。

    所有计算由 Canify Daemon 处理，CLI 只负责显示结果。
    """
    options = {"verbose": verbose, "strict": strict}
    exit_code = _run_validation_command("lint", path, options)
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

    所有计算由 Canify Daemon 处理，CLI 只负责显示结果。
    """
    options = {"verbose": verbose, "strict": strict}
    exit_code = _run_validation_command("verify", path, options)
    sys.exit(exit_code)


@app.command()
def validate(
    path: str = typer.Argument(
        ".",
        help="要验证的项目路径，默认为当前目录"
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        help="标签过滤表达式，例如 'core and not slow'"
    ),
    remote: bool = typer.Option(
        False,
        "--remote",
        help="包含远程执行的规则"
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
    执行 spec 规则的验证，支持标签过滤。

    执行项目中的业务规则验证，支持通过标签表达式灵活选择要执行的规则。
    """
    options = {
        "verbose": verbose,
        "strict": strict,
        "tags": tags,
        "remote": remote
    }
    exit_code = _run_validation_command("validate", path, options)
    sys.exit(exit_code)


def _run_validation_command(
    command: str,
    path: str,
    options: dict
) -> int:
    """
    运行验证命令的共享逻辑

    Args:
        command: 命令类型 ("lint", "verify", "validate")
        path: 目标路径
        options: 包含所有命令行选项的字典

    Returns:
        退出码
    """
    try:
        client = DaemonClient()

        # 检查 daemon 是否运行
        if not client.is_daemon_running():
            print("❌ Canify Daemon 未运行")
            print("请先运行: canify daemon start")
            return 1

        # 发送验证请求
        result = client.send_validation_request(
            command=command,
            target_path=path,
            working_directory=str(Path.cwd()),
            options=options
        )

        # 显示结果
        _display_validation_result(result, options.get("verbose", False))

        return 0 if result.get("success", False) else 1

    except Exception as e:
        print(f"❌ 执行 {command} 命令失败: {e}")
        return 1


def _display_validation_result(result: dict, verbose: bool) -> None:
    """
    显示验证结果

    Args:
        result: 验证结果
        verbose: 是否显示详细信息
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    success = result.get("success", False)
    error_count = len(result.get("errors", []))
    warning_count = len(result.get("warnings", []))

    if success:
        title = "✅ 验证通过"
        border_style = "green"
        message = f"- {warning_count} 个警告"
    else:
        title = "❌ 验证失败"
        border_style = "red"
        message = f"- {error_count} 个错误\n- {warning_count} 个警告"

    console.print(Panel.fit(
        f"[bold]{title}[/bold]\n{message}",
        title="验证结果",
        border_style=border_style
    ))

    # 显示详细诊断数据
    if verbose and result.get("verbose_data"):
        verbose_data = result["verbose_data"]
        if "symbol_table" in verbose_data:
            table = Table(title="符号表 (Symbol Table)", show_header=True, header_style="bold magenta")
            table.add_column("实体 ID", style="cyan", no_wrap=True)
            table.add_column("类型", style="green")
            table.add_column("名称", style="white")
            table.add_column("来源文件", style="dim")
            
            for symbol_id, symbol_info in verbose_data["symbol_table"].items():
                table.add_row(
                    symbol_id,
                    symbol_info.get("type", "-"),
                    symbol_info.get("name", "-"),
                    f"{symbol_info.get('file_path', '-')}:{symbol_info.get('start_line', '-')}"
                )
            console.print(table)

    # 显示警告详情
    if verbose and result.get("warnings"):
        table = Table(title="警告详情", show_header=True, header_style="bold yellow")
        table.add_column("位置", style="dim", width=25)
        table.add_column("警告描述", style="yellow")
        for warning in result["warnings"]:
            table.add_row(
                warning.get("location", "未知位置"),
                warning.get("message", "未知警告")
            )
        console.print(table)

    # 显示错误详情
    if result.get("errors"):
        table = Table(title="错误详情", show_header=True, header_style="bold red")
        table.add_column("位置", style="dim", width=25)
        table.add_column("错误描述", style="white")
        for error in result["errors"]:
            table.add_row(
                error.get("location", "未知位置"),
                error.get("message", "未知错误")
            )
        console.print(table)


# Daemon 命令组
daemon_app = typer.Typer(
    name="daemon", 
    help="管理 Canify Daemon",
    invoke_without_command=True
)

@daemon_app.callback()
def daemon_main(ctx: typer.Context):
    """
    管理 Canify Daemon。
    如果未提供子命令，则显示帮助信息。
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@daemon_app.command("start")
def daemon_start(
    project_path: str = typer.Argument(
        ".",
        help="要监控的项目路径，默认为当前目录"
    )
):
    """启动 Canify Daemon"""
    exit_code = daemon_command.run_daemon_start(project_path)
    sys.exit(exit_code)


@daemon_app.command("stop")
def daemon_stop():
    """停止 Canify Daemon"""
    exit_code = daemon_command.run_daemon_stop()
    sys.exit(exit_code)


@daemon_app.command("status")
def daemon_status(
    project_path: str = typer.Argument(
        ".",
        help="项目路径，默认为当前目录"
    )
):
    """显示 Canify Daemon 状态"""
    exit_code = daemon_command.run_daemon_status(project_path)
    sys.exit(exit_code)


# 注册 daemon 子命令
app.add_typer(daemon_app)


if __name__ == "__main__":
    app()