# Canify Agent Context

This document provides a complete overview of the Canify project for AI agent consumption. It includes the product plan, core architecture, technology stack, and architecture decisions.

---

# Canify: 产品开发计划书

版本: 1.0 日期: 2025 年 10 月 15 日

## 1. 产品名称：Canify

核心理念: 源自 "Canon" (正典, 准则)，意为将项目的知识和规则“正典化”。

双关含义: "Can-ify" -> "Make it
possible"，寓意本产品使能（empower）大规模、高质量的协作，使其成为可能。

## 2. 愿景与使命 (Vision & Mission)

愿景: 成为下一代知识密集型项目的协作基石，将“文档即代码”的理念推广到所有行业，实现真正意义上的、可验证的“单一事实来源”。

使命: 提供一个强大的、自动化的校验与协作系统，将软件工程中成熟的质量保证体系（类型检查、依赖管理、CI/CD）无缝融入到结构化文档的生命周期中，赋能团队以前所未有的效率和信心管理复杂信息。

## 3. 核心架构与设计决策

### 3.1. 混合数据管理模型

事实来源 (Source of Truth): 版本控制的文本文件。实体统一使用带有 YAML Front
Matter 的 Markdown 文件进行定义，确保变更历史的透明性、可审查性，与 Git 工作流完美兼容。

性能索引 (Performance
Index): 一个本地、非版本化的嵌入式数据库 (SQLite)。作为事实来源的只读缓存，为大规模项目提供毫秒级的查询性能，驱动 IDE/Agent 的实时交互体验。

### 3.2. 语法体系

- 实体声明: 使用围栏代码块 (Fenced Code Block) +
  YAML 的形式，以保证对所有标准 Markdown 渲染器的完美兼容性。
- 实体引用: 使用自定义协议的标准 Markdown 链接
  [链接文本](entity://<ENTITY_ID>)，实现跨文档的、健壮的语义链接。

### 3.3. 多阶段验证引擎

引擎的阶段保持不变，但每个阶段的职责在质量门中的应用被重新划分。

- 阶段一：符号发现: 快速扫描，建立全局实体 ID 符号表。
- 阶段二：图构建与循环检测: 构建实体引用有向图，检测致命的循环依赖。
- 阶段三：实体内部验证 (Intra-Entity
  Validation): 使用 Pydantic 模型对单个实体的字段进行完整的类型、格式和必填项校验。
- 阶段四：实体间交叉验证 (Inter-Entity
  Validation): 执行 constraints 目录中定义的、需要多个实体上下文的复杂业务逻辑校验（例如，数额加总、父子状态依赖等）。

### 3.4. 分级质量门

我们重新定义了 Lax 和 Strict 模式的职责，使其更加贴合开发者的心智模型。

#### 引入“占位符” (Placeholder) 语法

我们约定一个或多个特殊的字符串值（例如 "TBD", "TODO",
"?"）作为占位符。当一个字段的值是占位符时，它将被特定阶段的校验器有意地忽略。这允许开发者明确地标记一个实体是“故意不完整的”，而不是“意外错误的”。

#### Lax 模式 (用于 pre-commit 钩子)

目标: 保证提交到本地版本历史的每个实体自身是结构正确的，并且项目的引用网络是健全的。

执行:

- 阶段一：符号发现
- 阶段二：图构建与循环检测
- 阶段三：实体内部验证

特殊规则: 在执行阶段三（实体内部验证）时，如果一个字段的值是占位符（如 "TBD"），则跳过对该字段的校验。例如，一个 points 字段类型要求是整数，但如果开发者写入 points:
"TBD"，Lax 模式会放行。

结果: 开发者无法提交一个意外的类型错误（如 points:
"five"），但可以有意地提交一个未完成的实体（points:
"TBD"）。这既捕获了低级错误，又保护了 WIP 的灵活性。

#### Strict 模式 (用于 CI/CD pre-merge 钩子)

目标: 保证合并到主分支的代码库在逻辑上是完全自洽和完整的。

执行:

- 执行所有 Lax 模式的检查。
- 阶段四：实体间交叉验证。

特殊规则: Strict 模式禁止任何占位符的存在。在所有校验开始前，它会首先扫描是否存在 "TBD" 等值，如果发现，则立即报错。

结果: 任何未完成的工作（由占位符标记）都无法被合并，强制要求所有实体在进入主分支前必须达到“生产就绪”状态。

---

# Canify 核心架构规范

## 1. 数据模型规范

### 设计理念：引用与声明分离

为了在提供强大结构化能力的同时，最大程度地减少对用户阅读体验的干扰，我们采用了“引用-声明两阶段”范式。

1. **引用 (Reference)**: 在文档的正文中，通过自然的 Markdown 链接语法 `[链接文本](entity://<ENTITY_ID>)` 来引用实体。这使得引用点与上下文无缝融合。
2. **声明 (Declaration)**: 所有实体的具体定义都集中在文档末尾的“附录”区域，使用 `entity` 代码块进行声明。这种方式避免了在文档开头放置大段 YAML Front Matter，保持了正文的整洁。

### 实体声明格式 (Entity Declaration)

实体在 `entity` 类型的围栏代码块中，使用 YAML 格式进行定义。

**基本格式:**

````yaml
```entity
type: <string>       # 实体类型
id: <string>         # 唯一标识符
name: <string>       # 显示名称
# ... 其他自定义字段
```
````

**示例:**

````yaml
```entity
type: "project"
id: "canify-v1"
name: "Canify 核心功能开发"
budget: 50000
status: "active"
```
````

### 实体引用格式 (Entity Reference)

```markdown
[一个指向 Canify 项目的链接](entity://canify-v1)
```

**Pydantic 模型定义（推荐）:**

```python
from pydantic import BaseModel
from typing import Optional

class Project(BaseModel):
    id: str
    name: str
    type: str = "project"
    budget: Optional[float] = None
    status: str = "draft"

class Task(BaseModel):
    id: str
    name: str
    type: str = "task"
    project_id: str
    estimated_hours: Optional[float] = None
```

## 2. 接口规范

### CLI 命令接口

所有实现必须支持以下命令：

```bash
# 基础验证
canify validate [--mode=lax|strict] [--path=.] [--output=json|text]

# 查询功能
canify query <entity-id> [--fields=name,status,budget]
canify search "keyword" [--type=project|task]

# 缓存管理
canify cache rebuild

# 统计信息
canify stats
```

### 输出格式规范

**JSON 输出格式:**

```json
{
  "success": true,
  "errors": [
    {
      "entity_id": "project-123",
      "field": "budget",
      "message": "预算必须为数字",
      "severity": "error"
    }
  ],
  "warnings": [],
  "stats": {
    "total_entities": 150,
    "valid_entities": 148,
    "validation_time": "1.2s"
  }
}
```

## 3. 验证规则规范

### 四阶段验证流程

#### 阶段一：符号发现

- 输入：文件系统路径
- 输出：实体符号表
- 必须检测：重复实体 ID、无效实体类型

#### 阶段二：图构建

- 输入：实体符号表
- 输出：实体引用关系图
- 必须检测：循环依赖、无效引用

#### 阶段三：实体内部验证

- 输入：单个实体
- 输出：字段级错误
- 必须支持：类型检查、必填项、占位符处理

#### 阶段四：实体间交叉验证

- 输入：完整实体图
- 输出：业务规则违反
- 必须支持：自定义约束规则

### 占位符处理

```yaml
# Lax 模式：允许占位符
fields:
  budget: "TBD"    # 允许
  status: "TODO"   # 允许

# Strict 模式：禁止占位符
fields:
  budget: "TBD"    # 错误
  status: "TODO"   # 错误
```

## 4. 存储接口规范

### 文件系统接口

```bash
project/
├── entities/
│   ├── projects/
│   │   └── project-alpha.md
│   ├── tasks/
│   │   └── task-001.md
│   └── users/
│       └── user-john.md
└── constraints/
    └── business-rules.yaml
```

### 缓存数据库模式

```sql
-- 所有实现必须支持此模式或等效功能
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    content_json TEXT NOT NULL,
    file_path TEXT NOT NULL,
    -- 以下字段从 Git 历史恢复，不存储在 YAML 中
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    author TEXT,
    last_commit_hash TEXT
);

CREATE TABLE entity_references (
    from_entity_id TEXT,
    to_entity_id TEXT,
    reference_type TEXT
);
```

### Git 元数据恢复

系统应从 Git 提交历史自动恢复以下元数据：

- `created_at`: 文件首次提交时间
- `updated_at`: 文件最后修改时间
- `author`: 最后修改的作者
- `commit_hash`: 相关提交哈希

这些信息不应在 YAML Front Matter 中重复定义。

## 5. 配置规范

### 配置文件格式

```yaml
# .canify/config.yaml
storage:
  backend: sqlite|postgres|redis
  path: .canify/cache.db

validation:
  lax_mode:
    enabled: true
    skip_placeholder: true
  strict_mode:
    enabled: true
    require_complete: true

constraints:
  - type: budget_allocation
    rule: "sum(task.budget) <= project.budget"
  - type: status_dependency
    rule: "parent.status == 'active' => child.status != 'completed'"
```

## 6. 性能基准

所有实现必须满足以下性能要求：

- **小型项目** (100 实体): 验证时间 < 1 秒
- **中型项目** (1000 实体): 验证时间 < 5 秒
- **大型项目** (10000 实体): 验证时间 < 30 秒
- **查询性能**: 单实体查询 < 100ms

## 7. 测试规范

### 必须包含的测试用例

1.  **基础验证测试**

    - 有效实体通过验证
    - 无效实体被拒绝
    - 占位符处理正确

2.  **图构建测试**

    - 循环依赖检测
    - 无效引用检测
    - 复杂引用网络

3.  **业务规则测试**

    - 预算分配约束
    - 状态依赖约束
    - 自定义约束规则

4.  **性能测试**
    - 大规模实体验证
    - 缓存重建性能
    - 并发查询测试

## 8. 技术演进指南

### Python 原型阶段

**技术栈:**

- Python 3.9+
- Pydantic 2.0+
- Typer (CLI 框架)
- SQLAlchemy (数据库 ORM)
- GitPython (Git 集成)

**目标:** 快速验证核心概念，提供优秀的用户体验

### 性能优化阶段

当 Python 原型性能不足时：

1.  **Python 优化**

    - 使用 CPython 编译热点代码
    - 算法和数据结构优化
    - 并行处理大规模验证

2.  **Rust 热点重构**
    - 验证引擎用 Rust 重写
    - 大规模查询性能优化
    - 通过 PyO3 保持 Python 接口兼容

### 演进检查清单

- [ ] Python 原型完成核心功能验证
- [ ] Pydantic 模型定义体验良好
- [ ] 中小规模项目性能达标
- [ ] 用户能够轻松定义业务约束
- [ ] Agent 集成接口稳定

---

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
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 基础实体模型
│   │   │   ├── project.py      # 项目实体
│   │   │   └── task.py         # 任务实体
│   │   ├── validation/
│   │   │   ├── __init__.py
│   │   │   ├── discovery.py    # 符号发现
│   │   │   ├── graph.py        # 图构建
│   │   │   ├── intra.py        # 实体内部验证
│   │   │   └── inter.py        # 实体间验证
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── file_system.py  # 文件系统
│   │   │   ├── database.py     # 数据库
│   │   │   └── git_meta.py     # Git 元数据
│   │   └── integration/
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

1.  **算法优化**: 使用更高效的数据结构和算法
2.  **并行处理**: 使用 `asyncio` 和 `concurrent.futures`
3.  **缓存策略**: 实现智能缓存机制

### 阶段二：CPython 优化

1.  **热点分析**: 使用 profiling 工具识别性能瓶颈
2.  **CPython 编译**: 将关键函数编译为 C 扩展
3.  **类型声明**: 添加静态类型提示提升性能

### 阶段三：Rust 重构

1.  **验证引擎**: 用 Rust 重写四阶段验证
2.  **查询优化**: 大规模查询性能优化
3.  **Python 绑定**: 使用 PyO3 保持接口兼容

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

---

# Canify 架构决策记录 (ADR)

版本: 1.0 日期: 2025-10-16

## 决策概览

| 决策编号 | 决策主题     | 状态   | 日期       |
| -------- | ------------ | ------ | ---------- |
| ADR-001  | 编程语言选择 | 已确定 | 2025-10-16 |
| ADR-002  | 存储架构设计 | 已确定 | 2025-10-16 |
| ADR-003  | 验证引擎架构 | 已确定 | 2025-10-16 |
| ADR-004  | CLI 接口设计 | 已确定 | 2025-10-16 |

---

## ADR-001: 编程语言选择

### 状态

已确定 - 采用 Python + Pydantic，备选 Rust 热点优化

### 上下文

Canify 需要用户友好的实体定义体验，同时需要良好的 Agent 集成能力。用户更倾向于使用 Pydantic 来表达业务意图。

### 决策

#### 首选：Python + Pydantic

- 理由：Pydantic 提供优秀的用户体验、类型提示、丰富的验证生态
- 优势：快速原型、团队熟悉度、Agent 友好
- 策略：Python 原型验证价值，热点代码后续用 Rust 优化

#### 备选：Rust 热点优化

- 时机：当性能成为瓶颈时
- 范围：验证引擎、大规模查询等性能关键路径
- 原则：保持 Python 接口兼容性

### 后果

- 初期开发速度更快，用户体验更好
- 性能优化路径清晰，可渐进式改进
- 保持与 Pydantic 生态的紧密集成

---

## ADR-002: 存储架构设计

### 状态

已确定

### 上下文

需要同时支持版本控制的文本文件和高效的查询性能。

### 决策

采用分层存储架构：

1.  **事实来源**: Markdown + YAML Front Matter 文件
2.  **性能缓存**: SQLite 数据库
3.  **企业扩展**: PostgreSQL/Redis (可选)

### 后果

- 数据一致性需要精心设计
- 缓存失效策略是关键
- 支持渐进式扩展

---

## ADR-003: 验证引擎架构

### 状态

已确定

### 上下文

需要支持渐进式验证，从基础语法检查到复杂业务规则验证。

### 决策

四阶段验证引擎：

1.  **符号发现**: 快速扫描建立实体符号表
2.  **图构建**: 构建实体引用关系图，检测循环依赖
3.  **实体内部验证**: 类型、格式、必填项校验
4.  **实体间交叉验证**: 复杂业务逻辑校验

### 后果

- 验证性能需要优化
- 错误消息需要结构化设计
- 支持 Lax/Strict 模式

---

## ADR-004: CLI 接口设计

### 状态

已确定

### 上下文

需要提供用户友好的命令行接口，同时支持 Agent 自动化集成。

### 决策

核心命令集：

- `validate`: 验证命令
- `query`: 查询命令
- `search`: 搜索命令
- `hook`: Agent 集成钩子

### 后果

- 输出格式需要支持 JSON/text
- 错误码需要标准化
- 配置系统需要灵活

---

## 技术演进指南

### 性能优化路径

当 Python 原型性能不足时，按以下路径优化：

1.  **第一阶段：Python 优化**

    - 使用 CPython 编译热点代码
    - 优化算法和数据结构
    - 并行处理大规模验证

2.  **第二阶段：Rust 热点重构**
    - 验证引擎用 Rust 重写
    - 大规模查询性能优化
    - 通过 Python 绑定保持接口兼容

### 成功标准

- Python 原型在 2 周内完成核心功能验证
- 中小规模项目（1000 实体）验证时间 < 5 秒
- 用户能够使用 Pydantic 轻松定义实体模型
