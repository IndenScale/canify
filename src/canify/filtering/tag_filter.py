"""
标签过滤器

负责根据布尔表达式过滤 spec 规则。
"""

import logging
import re
from collections.abc import Callable
from typing import Any

from ..models.spec import SpecificationRule

logger = logging.getLogger(__name__)


class TagFilter:
    """标签过滤器"""

    def __init__(self):
        """初始化过滤器"""
        self.operators = {
            'and': self._and_operator,
            'or': self._or_operator,
            'not': self._not_operator
        }

    def filter_specs(self, specs: list[SpecificationRule], expression: str) -> list[SpecificationRule]:
        """
        根据布尔表达式过滤 spec 规则

        Args:
            specs: spec 规则列表
            expression: 布尔表达式，例如 "core and not slow"

        Returns:
            过滤后的 spec 规则列表
        """
        if not expression:
            return specs

        try:
            # 简化的表达式解析
            filter_func = self._simple_parse_expression(expression)

            # 应用过滤器
            filtered_specs = [spec for spec in specs if filter_func(spec)]

            logger.info(f"使用表达式 '{expression}' 过滤了 {len(filtered_specs)}/{len(specs)} 个 spec 规则")
            return filtered_specs

        except Exception as e:
            logger.error(f"过滤 spec 规则失败: {e}")
            return specs

    def _parse_expression(self, expression: str) -> Callable[[SpecificationRule], bool]:
        """
        解析布尔表达式并返回过滤函数

        Args:
            expression: 布尔表达式

        Returns:
            过滤函数
        """
        # 预处理表达式：转换为小写，处理空格
        expr = expression.lower().strip()

        # 处理括号分组
        expr = self._handle_parentheses(expr)

        # 解析表达式
        return self._parse_logical_expression(expr)

    def _handle_parentheses(self, expression: str) -> str:
        """
        处理括号分组

        Args:
            expression: 表达式

        Returns:
            处理后的表达式
        """
        # 简单的括号处理：将括号内的内容视为一个整体
        # 在实际实现中，可能需要更复杂的解析器
        return expression

    def _parse_logical_expression(self, expression: str) -> Callable[[SpecificationRule], bool]:
        """
        解析逻辑表达式

        Args:
            expression: 逻辑表达式

        Returns:
            过滤函数
        """
        # 分割表达式为 tokens
        tokens = self._tokenize_expression(expression)

        # 构建抽象语法树
        ast = self._build_ast(tokens)

        # 生成过滤函数
        return self._generate_filter_function(ast)

    def _tokenize_expression(self, expression: str) -> list[str]:
        """
        将表达式分割为 tokens

        Args:
            expression: 表达式

        Returns:
            token 列表
        """
        # 使用正则表达式分割
        # 匹配单词、操作符和括号
        pattern = r'\b(and|or|not)\b|\(|\)|[^\s()]+'
        tokens = re.findall(pattern, expression)

        # 过滤空字符串
        tokens = [token.strip() for token in tokens if token.strip()]

        return tokens

    def _build_ast(self, tokens: list[str]) -> Any:
        """
        构建抽象语法树

        Args:
            tokens: token 列表

        Returns:
            抽象语法树
        """
        # 简化的 AST 构建
        # 在实际实现中，可能需要更复杂的解析器

        if len(tokens) == 1:
            # 单个标签
            return {'type': 'tag', 'value': tokens[0]}

        # 处理 not 操作符
        if tokens[0] == 'not' and len(tokens) == 2:
            return {
                'type': 'operator',
                'operator': 'not',
                'left': self._build_ast([tokens[1]])
            }

        # 处理二元操作符
        for i, token in enumerate(tokens):
            if token in ['and', 'or']:
                left_tokens = tokens[:i]
                right_tokens = tokens[i+1:]

                # 确保左右两侧都有内容
                if left_tokens and right_tokens:
                    return {
                        'type': 'operator',
                        'operator': token,
                        'left': self._build_ast(left_tokens),
                        'right': self._build_ast(right_tokens)
                    }

        # 默认返回第一个 token
        return {'type': 'tag', 'value': tokens[0]}

    def _generate_filter_function(self, ast: Any) -> Callable[[SpecificationRule], bool]:
        """
        根据抽象语法树生成过滤函数

        Args:
            ast: 抽象语法树

        Returns:
            过滤函数
        """
        if ast['type'] == 'tag':
            tag = ast['value'].lower()
            return lambda spec: bool(spec.tags and tag in [t.lower() for t in spec.tags])

        elif ast['type'] == 'operator':
            operator = ast['operator']
            left_func = self._generate_filter_function(ast['left'])

            if operator == 'not':
                return lambda spec: not left_func(spec)

            elif operator in ['and', 'or']:
                right_func = self._generate_filter_function(ast['right'])

                if operator == 'and':
                    return lambda spec: left_func(spec) and right_func(spec)
                elif operator == 'or':
                    return lambda spec: left_func(spec) or right_func(spec)

        # 默认返回 True
        return lambda spec: True

    def _simple_parse_expression(self, expression: str) -> Callable[[SpecificationRule], bool]:
        """
        简化的表达式解析器

        Args:
            expression: 布尔表达式

        Returns:
            过滤函数
        """
        expr = expression.lower().strip()

        # 处理 "and" 表达式
        if " and " in expr:
            parts = expr.split(" and ")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()

                # 处理 "not" 操作符
                if right.startswith("not "):
                    tag = right[4:].strip()
                    return lambda spec: (
                        self._has_tag(spec, left) and
                        not self._has_tag(spec, tag)
                    )
                else:
                    return lambda spec: (
                        self._has_tag(spec, left) and
                        self._has_tag(spec, right)
                    )
            # 如果分割后不是2部分，回退到单个标签
            else:
                return lambda spec: self._has_tag(spec, expr)

        # 处理 "or" 表达式
        elif " or " in expr:
            parts = expr.split(" or ")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                return lambda spec: (
                    self._has_tag(spec, left) or
                    self._has_tag(spec, right)
                )
            # 如果分割后不是2部分，回退到单个标签
            else:
                return lambda spec: self._has_tag(spec, expr)

        # 处理 "not" 表达式
        elif expr.startswith("not "):
            tag = expr[4:].strip()
            return lambda spec: not self._has_tag(spec, tag)

        # 单个标签
        else:
            return lambda spec: self._has_tag(spec, expr)

    def _has_tag(self, spec: SpecificationRule, tag: str) -> bool:
        """
        检查 spec 是否包含指定标签

        Args:
            spec: spec 规则
            tag: 标签

        Returns:
            是否包含标签
        """
        if not spec.tags:
            return False

        tag_lower = tag.lower()
        return any(t.lower() == tag_lower for t in spec.tags)

    def _and_operator(self, left: Callable, right: Callable) -> Callable:
        """AND 操作符"""
        return lambda spec: left(spec) and right(spec)

    def _or_operator(self, left: Callable, right: Callable) -> Callable:
        """OR 操作符"""
        return lambda spec: left(spec) or right(spec)

    def _not_operator(self, operand: Callable) -> Callable:
        """NOT 操作符"""
        return lambda spec: not operand(spec)

    def validate_expression(self, expression: str) -> bool:
        """
        验证表达式是否有效

        Args:
            expression: 布尔表达式

        Returns:
            表达式是否有效
        """
        try:
            self._parse_expression(expression)
            return True
        except Exception:
            return False

    def get_available_operators(self) -> list[str]:
        """
        获取可用的操作符

        Returns:
            操作符列表
        """
        return list(self.operators.keys())