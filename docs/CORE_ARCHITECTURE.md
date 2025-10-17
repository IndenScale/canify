# Canify 核心架构规范

## 1. 数据模型规范

### 设计理念：引用与声明分离

为了在提供强大结构化能力的同时，最大程度地减少对用户阅读体验的干扰，我们采用了“引用-声明两阶段”范式。

1. **引用 (Reference)**: 在文档的正文中，通过自然的 Markdown 链接语法 `[链接文本](entity://<ENTITY_ID>)` 来引用实体。这使得引用点与上下文无缝融合。
2. **声明 (Declaration)**: 所有实体的具体定义都集中在文档末尾的“附录”区域，使用 `entity` 代码块进行声明。这种方式避免了在文档开头放置大段 YAML Front Matter，保持了正文的整洁。

Canify 可以通过 glob 模式发现散落在多个文件中的实体，例如 `canify verify 'demo/**/*.md'`，从而支持跨文件的引用和声明。

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

## 2. 核心架构：统一验证引擎

Canify 的核心是一个统一的验证引擎 (`ValidationEngine`)。所有的核心命令 (`lint`, `verify`, `validate`) 都共享这个引擎，通过传入不同的参数来调整其行为，从而实现分层验证策略。

这种设计的优势在于：

- **代码复用**: 所有验证逻辑集中在一处，易于维护和扩展。
- **行为一致**: 不同命令之间的验证行为有清晰的继承关系，而非各自为政。
- **配置灵活**: 可以通过简单的参数调整（`mode` 和 `strict`）来改变验证的深度和严格性。

### CLI 命令接口

Canify 提供三个核心命令，以适应不同的开发阶段和需求。它们本质上是调用同一个验证引擎的不同“预设模式”。

| 命令              | `mode` 参数  | `strict` 参数 | 核心职责                                       | 典型场景        |
| :---------------- | :----------- | :------------ | :--------------------------------------------- | :-------------- |
| `canify lint`     | `"lint"`     | `False`       | 提供实时、快速的语法和风格检查。               | **编辑时**      |
| `canify verify`   | `"verify"`   | `False`       | 保证结构和引用的完整性，但允许占位符。         | **提交时**      |
| `canify validate` | `"validate"` | `True` (默认) | 执行最严格的检查，包括业务规则，且禁止占位符。 | **合并/发布前** |

### 验证引擎的四个阶段

`ValidationEngine` 的执行过程分为四个连续的阶段，确保了验证的系统性和全面性。

#### 阶段一：符号发现 (Symbol Discovery)

- **目标**: 扫描所有 Markdown 文件，解析出全部的实体声明 (`EntityDeclaration`)。
- **核心任务**:
  - 解析 ` ```entity ` 代码块。
  - 检查并报告**重复的实体 ID**。
  - 检查实体是否包含 `type`, `id`, `name` 等基本字段。
- **输出**: 一个初步的**符号表 (Symbol Table)**，包含了项目中所有已声明的实体。

#### 阶段二：引用验证 (Reference Validation)

- **目标**: 解析所有的实体引用 (`EntityReference`)，并确保它们的有效性。
- **核心任务**:
  - 解析 `[...](entity://...)` 链接。
  - 检查并报告**悬空引用**（即链接到不存在的实体 ID）。
  - 检查并报告**循环依赖**。
- **输出**: 一个包含实体间完整引用关系的符号表。

#### 阶段三：Schema 验证 (Schema Validation)

- **目标**: 验证每个实体的数据类型和格式是否正确。
- **核心任务**:
  - **类型检查**: 确保字段值（如 `budget`）符合预期的类型（如 `number`）。
  - **值约束**: 确保字段值（如 `status`）在预设的有效选项列表内。
  - **占位符处理**:
    - 在 `verify` 模式下，占位符 (如 "TBD", "TODO") 被识别并**豁免**类型检查，仅产生**警告**。
    - 在 `validate` 模式下，任何占位符都会被报告为**错误**。

#### 阶段四：业务规则验证 (Business Rule Validation)

- **目标**: 执行用户定义的、跨实体的复杂业务逻辑。
- **核心任务**:
  - 查找并解析项目根目录下的 `constraints/spec_*.yaml` 文件。
  - 根据 `spec` 文件中定义的规则，动态加载并执行对应的 Python 测试函数（位于 `constraints/test_cases/`）。
  - 根据规则中为当前 `mode` (`verify` 或 `validate`) 定义的严重级别，将违反情况报告为**警告**或**错误**。
  - 例如，检查“所有任务的总预算不能超过项目预算”。

### 占位符处理

```yaml
# Lax 模式 (verify 命令): 允许占位符
fields:
  budget: "TBD"    # 允许
  status: "TODO"   # 允许

# Strict 模式 (validate 命令): 禁止占位符
fields:
  budget: "TBD"    # 错误
  status: "TODO"   # 错误
```

## 5. 存储接口规范

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

## 6. 配置规范

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

## 7. 性能基准

所有实现必须满足以下性能要求：

- **小型项目** (100 实体): 验证时间 < 1 秒
- **中型项目** (1000 实体): 验证时间 < 5 秒
- **大型项目** (10000 实体): 验证时间 < 30 秒
- **查询性能**: 单实体查询 < 100ms

## 8. 测试规范

### 必须包含的测试用例

1. **基础验证测试**

   - 有效实体通过验证
   - 无效实体被拒绝
   - 占位符处理正确

2. **图构建测试**

   - 循环依赖检测
   - 无效引用检测
   - 复杂引用网络

3. **业务规则测试**

   - 预算分配约束
   - 状态依赖约束
   - 自定义约束规则

4. **性能测试**
   - 大规模实体验证
   - 缓存重建性能
   - 并发查询测试

## 9. 技术演进指南

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

1. **Python 优化**

   - 使用 CPython 编译热点代码
   - 算法和数据结构优化
   - 并行处理大规模验证

2. **Rust 热点重构**
   - 验证引擎用 Rust 重写
   - 大规模查询性能优化
   - 通过 PyO3 保持 Python 接口兼容

### 演进检查清单

- [ ] Python 原型完成核心功能验证
- [ ] Pydantic 模型定义体验良好
- [ ] 中小规模项目性能达标
- [ ] 用户能够轻松定义业务约束
- [ ] Agent 集成接口稳定
