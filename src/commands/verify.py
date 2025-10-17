"""
Canify verify 命令
"""

from .utils import run_validation_pipeline

def run_verify(path: str, verbose: bool = False, strict: bool = False) -> int:
    """
    运行 verify 命令。
    """
    return run_validation_pipeline(path, verbose, mode="verify", strict=strict)