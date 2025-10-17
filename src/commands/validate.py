"""
Canify validate 命令
"""

from .utils import run_validation_pipeline

def run_validate(path: str, verbose: bool = False, strict: bool = False) -> int:
    """
    运行 validate 命令。
    """
    return run_validation_pipeline(path, verbose, mode="validate", strict=strict)
