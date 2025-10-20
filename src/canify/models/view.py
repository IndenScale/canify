"""
Canify 视图 (View) 模型
"""
from typing import List, Dict
from pydantic import BaseModel, Field

from .spec import SpecificationRule
from .entity_declaration import EntityDeclaration
from .entity_reference import EntityReference


class View(BaseModel):
    """
    表示一个特定检查点（Checkpoint）的知识库完整状态。
    这是在 CLI 和 Server 之间传递的核心数据结构。
    """
    branch: str = Field(..., description="视图所属的 Git 分支")
    checkpoint_id: str = Field(..., description="视图的唯一标识符 (例如，commit hash 或时间戳)")

    entities: Dict[str, EntityDeclaration] = Field(
        default_factory=dict, 
        description="知识库中所有实体的集合，以实体ID为键"
    )

    references: List[EntityReference] = Field(
        default_factory=list, 
        description="知识库中所有的实体引用"
    )

    specs: List[SpecificationRule] = Field(
        default_factory=list, 
        description="知识库中所有的业务规则约束"
    )

    # 模式（Schema）是 Python 代码（Pydantic 模型），不是纯粹的数据，
    # 因此在视图中我们只传递它们的名称作为标识。
    # Server 端负责加载和管理实际的 Schema 类。
    schema_names: List[str] = Field(
        default_factory=list, 
        description="已加载的所有实体模式（Schema）的名称"
    )

    class Config:
        frozen = True
