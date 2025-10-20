"""
Canify version 命令

显示 Canify 版本信息。
"""

from rich.console import Console


def run_version() -> int:
    """
    运行 version 命令

    Returns:
        退出码：总是返回 0
    """
    console = Console()
    console.print("Canify v0.2.0-dev")
    return 0