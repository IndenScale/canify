"""
位置信息模型

记录代码元素在文件中的具体位置，用于错误定位。
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    """
    位置信息模型
    """
    file_path: Path = Field(..., description="文件路径")
    start_line: int = Field(..., description="起始行号（从1开始）")
    end_line: int = Field(..., description="结束行号（从1开始）")
    start_column: Optional[int] = Field(None, description="起始列号")
    end_column: Optional[int] = Field(None, description="结束列号")

    def __str__(self) -> str:
        """
        生成用户友好的位置描述

        Returns:
            位置描述字符串
        """
        if self.start_column and self.end_column:
            return f"{self.file_path}:{self.start_line}:{self.start_column}-{self.end_line}:{self.end_column}"
        elif self.start_line == self.end_line:
            return f"{self.file_path}:{self.start_line}"
        else:
            return f"{self.file_path}:{self.start_line}-{self.end_line}"
