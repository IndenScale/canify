# Canify 技术栈文档

## 核心技术选型

### 编程语言：Python 3.9+

**理由：**

- Pydantic 提供优秀的类型安全和验证体验
- 丰富的生态系统和库支持
- 团队熟悉度，降低学习曲线
- Agent 友好，易于集成

### 核心依赖

#### 数据模型与验证

- **Pydantic 2.0+**: 实体模型定义和验证
- **PyYAML**: 实体代码块 (YAML) 解析

#### CLI 框架

- **Typer**: 现代 CLI 框架，类型安全
- **Rich**: 终端输出美化

#### 数据存储

- **SQLAlchemy**: 数据库 ORM，支持多种后端
- **SQLite**: 默认缓存数据库
- **GitPython**: Git 集成，元数据恢复

#### 异步与性能

- **asyncio**: 异步 I/O 支持
- **aiofiles**: 异步文件操作
- **CPython**: 性能热点优化（可选）

## 项目结构

```bash
canify/
├── src/
│   ├── canify/
│   │   ├── __init__.py
│   │   ├── cli.py              # CLI 入口
│   │   ├── models/             # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 基础实体模型
│   │   │   ├── project.py      # 项目实体
│   │   │   └── task.py         # 任务实体
│   │   ├── validation/         # 验证引擎
│   │   │   ├── __init__.py
│   │   │   ├── discovery.py    # 符号发现
│   │   │   ├── graph.py        # 图构建
│   │   │   ├── intra.py        # 实体内部验证
│   │   │   └── inter.py        # 实体间验证
│   │   ├── storage/            # 存储层
│   │   │   ├── __init__.py
│   │   │   ├── file_system.py  # 文件系统
│   │   │   ├── database.py     # 数据库
│   │   │   └── git_meta.py     # Git 元数据
│   │   └── integration/        # 集成层
│   │       ├── __init__.py
│   │       ├── hooks.py        # 钩子系统
│   │       └── agent.py        # Agent 集成
│   ├── tests/                  # 测试
│   └── docs/                   # 文档
├── pyproject.toml              # 项目配置
└── README.md
```

## 核心实现示例

### 实体模型定义

```python
# src/canify/models/base.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class CanifyEntity(BaseModel):
    """基础实体模型"""
    id: str = Field(..., description="实体唯一标识符")
    name: str = Field(..., description="实体显示名称")
    type: str = Field(..., description="实体类型")

    # 从 Git 恢复的元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None

    class Config:
        extra = "allow"  # 允许额外字段

# src/canify/models/project.py
class Project(CanifyEntity):
    """项目实体"""
    type: str = "project"
    budget: Optional[float] = None
    status: str = "draft"
    deadline: Optional[datetime] = None
```

### CLI 实现

```python
# src/canify/cli.py
import typer
from typing import Optional
from pathlib import Path

app = typer.Typer(help="Canify - 结构化文档验证工具")

@app.command()
def validate(
    path: Path = typer.Argument(".", help="项目路径"),
    mode: str = typer.Option("lax", help="验证模式: lax|strict"),
    output: str = typer.Option("text", help="输出格式: text|json")
):
    """验证项目实体"""
    # 实现验证逻辑
    pass

@app.command()
def query(
    entity_id: str = typer.Argument(..., help="实体ID"),
    fields: Optional[str] = typer.Option(None, help="查询字段")
):
    """查询实体信息"""
    # 实现查询逻辑
    pass

if __name__ == "__main__":
    app()
```

### 验证引擎

```python
# src/canify/validation/discovery.py
from pathlib import Path
from typing import List, Dict
import yaml

class SymbolDiscovery:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.entities: Dict[str, Dict] = {}

    def discover_entities(self) -> List[Dict]:
        """发现项目中的所有实体"""
        entities = []
        for file_path in self.root_path.rglob("*.md"):
            entity = self.parse_entity_file(file_path)
            if entity:
                entities.append(entity)
        return entities

    def parse_entity_file(self, file_path: Path) -> Optional[Dict]:
        """解析实体文件"""
        content = file_path.read_text(encoding="utf-8")

        # 提取 YAML Front Matter
        if content.startswith("---\
"):
            parts = content.split("---\
", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                try:
                    entity_data = yaml.safe_load(yaml_content)
                    entity_data["file_path"] = str(file_path)
                    return entity_data
                except yaml.YAMLError:
                    return None
        return None
```

## 开发环境设置

### 依赖安装

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"
```

### 项目配置 (pyproject.toml)

```toml
[project]
name = "canify"
version = "0.1.0"
description = "结构化文档验证工具"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "black",
    "isort",
    "mypy",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 性能优化路径

### 阶段一：Python 优化

1. **算法优化**: 使用更高效的数据结构和算法
2. **并行处理**: 使用 `asyncio` 和 `concurrent.futures`
3. **缓存策略**: 实现智能缓存机制

### 阶段二：CPython 优化

1. **热点分析**: 使用 profiling 工具识别性能瓶颈
2. **CPython 编译**: 将关键函数编译为 C 扩展
3. **类型声明**: 添加静态类型提示提升性能

### 阶段三：Rust 重构

1. **验证引擎**: 用 Rust 重写四阶段验证
2. **查询优化**: 大规模查询性能优化
3. **Python 绑定**: 使用 PyO3 保持接口兼容

## 测试策略

### 单元测试

- 实体模型验证
- 文件解析测试
- 验证规则测试

### 集成测试

- 端到端验证流程
- Git 集成测试
- Agent 钩子测试

### 性能测试

- 大规模实体验证性能
- 缓存重建性能
- 并发查询性能
