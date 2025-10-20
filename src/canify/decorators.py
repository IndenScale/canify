"""
Canify 装饰器

提供用于标记 fixture 和 test_case 函数的装饰器。
"""

from typing import Callable, Any, TypeVar

T = TypeVar('T', bound=Callable[..., Any])


def fixture(func: T) -> T:
    """
    标记一个函数为 canify fixture

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    func._canify_fixture = True
    return func


def test_case(func: T) -> T:
    """
    标记一个函数为 canify test_case

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    func._canify_test_case = True
    return func