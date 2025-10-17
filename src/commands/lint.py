"""
Canify lint 命令
"""

from .utils import run_validation_pipeline

def run_lint(path: str, verbose: bool = False) -> int:
    """
    运行 lint 命令，协调所有 linting 任务。
    """
    # 未来可在此处添加外部工具调用
    return run_validation_pipeline(path, verbose, mode="lint", strict=False)
