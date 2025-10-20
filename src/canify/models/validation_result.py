"""
验证结果模型

表示验证引擎的执行结果。
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from .location import Location


class ValidationSeverity(str, Enum):
    """验证严重级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationError(BaseModel):
    """
    验证错误模型
    """
    rule_id: str = Field(..., description="规则标识符")
    message: str = Field(..., description="错误消息")
    severity: ValidationSeverity = Field(..., description="严重级别")
    location: Optional[Location] = Field(None, description="错误位置")
    entity_id: Optional[str] = Field(None, description="相关实体ID")

    def __str__(self) -> str:
        """生成错误描述的字符串表示"""
        location_str = f"在 {self.location}" if self.location else ""
        entity_str = f" (实体: {self.entity_id})" if self.entity_id else ""
        return f"[{self.severity.upper()}] {self.rule_id}: {self.message}{location_str}{entity_str}"


class ValidationResult(BaseModel):
    """
    验证结果模型
    """
    success: bool = Field(..., description="验证是否成功")
    errors: List[ValidationError] = Field(default_factory=list, description="验证错误列表")
    warnings: List[ValidationError] = Field(default_factory=list, description="验证警告列表")
    total_checks: int = Field(default=0, description="执行的检查总数")
    verbose_data: Optional[dict] = Field(None, description="详细的诊断数据")

    def add_error(self, error: ValidationError) -> None:
        """添加错误"""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: ValidationError) -> None:
        """添加警告"""
        self.warnings.append(warning)

    def merge(self, other: 'ValidationResult') -> None:
        """合并另一个验证结果"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.total_checks += other.total_checks
        if not other.success:
            self.success = False

    @classmethod
    def success_result(cls) -> 'ValidationResult':
        """创建成功的验证结果"""
        return cls(success=True)

    @classmethod
    def failure_result(cls) -> 'ValidationResult':
        """创建失败的验证结果"""
        return cls(success=False)