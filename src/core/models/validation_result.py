"""
验证结果模型

存储验证过程的完整结果。
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .location import Location
from .symbol_table import SymbolTable


class ValidationError(BaseModel):
    """
    验证错误模型

    表示在验证过程中发现的错误。
    """
    severity: str = Field(..., description="错误严重程度")
    message: str = Field(..., description="错误消息")
    location: Optional[Location] = Field(None, description="错误位置")
    entity_id: Optional[str] = Field(None, description="相关实体ID")
    error_type: str = Field(..., description="错误类型")

    def __str__(self) -> str:
        """
        生成错误描述的字符串表示

        Returns:
            错误描述字符串
        """
        location_str = str(self.location) if self.location else "unknown location"
        return f"[{self.severity.upper()}] {self.error_type}: {self.message} at {location_str}"


class ValidationResult(BaseModel):
    """
    验证结果模型
    """
    success: bool = Field(..., description="验证是否成功")
    errors: list[ValidationError] = Field(default_factory=list, description="验证错误列表")
    warnings: list[ValidationError] = Field(default_factory=list, description="验证警告列表")
    symbol_table: Optional[SymbolTable] = Field(None, description="符号表")

    def add_error(self, error: ValidationError) -> None:
        """
        添加错误到验证结果

        Args:
            error: 要添加的错误
        """
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: ValidationError) -> None:
        """
        添加警告到验证结果

        Args:
            warning: 要添加的警告
        """
        self.warnings.append(warning)

    @property
    def total_issues(self) -> int:
        """
        获取问题总数（错误+警告）

        Returns:
            问题总数
        """
        return len(self.errors) + len(self.warnings)