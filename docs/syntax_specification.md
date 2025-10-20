# 语法规约 (Syntax Specification)

本文档详细定义了 Canify 生态系统中所有核心构件 (Artifacts) 的语法规范。

---

## 1. 实体声明 (Entity Declaration)

实体是项目知识图谱中的核心节点。

- **位置**: Markdown (`.md`) 文件的尾部。
- **格式**: 使用一个语言类型为 `entity` 的代码块包裹，代码块内部为标准 YAML 格式。
- **实体类型命名**: 实体类型 (`type` 字段) 必须使用**首字母大写**的命名方式，与对应的 Pydantic 模型类名保持一致。例如：`User`, `Project`, `Service`, `Task`。

- **示例**: 在一个名为 `user-api.md` 的文件中：

```markdown
# User API Service

这里是关于该服务的详细描述文档...

该服务由 [DevOps 团队](entity://team-devops) 负责维护。

```entity
id: service-user-api
type: Service
name: User API Service
description: Handles user authentication and profile management.
owner: entity://team-devops
tier: 2
```

## 2. 实体引用 (Entity Reference)

实体引用用于在实体之间建立链接。

### 2.1 文本引用 (Link Reference)

- **位置**: Markdown (`.md`) 文件的主体内容中。
- **格式**: 使用标准的 Markdown 链接语法，但协议 (protocol) 为 `entity://`。
    - 语法: `[链接文本](entity://<目标实体ID>)`

- **示例**:

```markdown
The User API is managed by the [DevOps Team](entity://team-devops).
```

### 2.2 字段引用 (Field Reference)

- **位置**: 在 ` ```entity ` 代码块内部，作为某个字段的值。
- **格式**: 一个以 `entity://` 协议开头的字符串。
    - 语法: `字段名: entity://<目标实体ID>`

- **示例**:

```yaml
```entity
id: service-user-api
type: Service
name: User API Service
owner: entity://team-devops
```

## 3. 模式定义 (Schema Definition)

模式定义了特定类型实体的数据结构、字段和类型。

- **位置**: Python (`.py`) 文件中。
- **格式**: 一个继承自 Pydantic `BaseModel` 的 Python 类。**类名即为实体类型 (`entity_type`)**。
- **字段类型**: 支持所有标准的 Python 类型 (`str`, `int`, `list`, `dict` 等) 和 Pydantic 提供的特殊类型。
- **引用类型**: 为了实现对实体引用的类型安全检查，应使用 `canify.types` 中提供的特殊注解。
    - `from canify.types import CanifyReference, Ref, Annotated`
    - `owner: Annotated[CanifyReference, Ref("Team")]`
    - 这段注解表示 `owner` 字段必须是一个实体引用，并且该引用指向的实体类型必须是 `Team`（注意使用首字母大写的实体类型名称）。
- **自定义验证器**: 支持使用 Pydantic 的 `@field_validator` 装饰器来添加更复杂的字段验证逻辑。

### 示例

在一个名为 `models.py` 的文件中：

```python
from pydantic import BaseModel, field_validator
from typing import Annotated
from canify.types import CanifyReference, Ref

class Service(BaseModel):
    id: str
    type: str
    name: str
    description: str | None = None
    owner: Annotated[CanifyReference, Ref("team")]
    tier: int

    @field_validator("tier")
    def tier_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Tier must be a positive integer")
        return v
```

## 4. 规约定义 (Spec Definition)

规约用于定义项目的业务规则和高级约束。

- **位置**: YAML 文件，其名称必须以 `spec_` 开头 (例如, `spec_business_rules.yaml`)。
- **根元素**: 文件必须包含一个名为 `specs` 的顶层列表。
- **规约字段**:
    - `id` (`string`): 规则的全局唯一 ID。
    - `name` (`string`): 规则的可读名称。
    - `description` (`string`, 可选): 对规则的详细文字说明。
    - `levels` (`dict`): 定义规则在不同验证命令下的严重级别。键为命令名 (`verify`, `validate`)，值为级别 (`error`, `warning`)。
    - `fixture` (`string`): 指向一个 Python 函数的完整导入路径 (例如 `my_project.fixtures.get_all_services`)。此函数负责准备验证所需的数据。
    - `test_case` (`string`): 指向一个 Python 函数的完整导入路径 (例如 `my_project.tests.check_service_owner`)。此函数接收 `fixture` 的数据并执行验证逻辑。
    - `env` (`string`, 可选, 默认: `local`): 规则的执行环境，可以是 `local` 或 `remote`。
    - `tags` (`list[string]`, 可选): 用于对规则进行分类和过滤的标签列表。

### 示例

在一个名为 `spec_project_rules.yaml` 的文件中：

```yaml
specs:
  - id: rule-service-must-have-owner
    name: All services must have an owner
    description: >
      Ensures that every service entity has a valid owner team assigned.
    levels:
      verify: warning
      validate: error
    fixture: "demo.constraints.test_cases.project_rules.get_all_services"
    test_case: "demo.constraints.test_cases.project_rules.check_owner_exists"
    tags:
      - core
      - service-management
```

## 5. 标签过滤表达式 (Tag Filtering Expression)

- **位置**: 用于 `canify validate` 命令的 `--tags` 选项。
- **格式**: 一个包含标签名和操作符的字符串。
- **支持的操作符**: `and`, `or`, `not`。
- **优先级**: 当前实现中，`and` 的优先级高于 `or`。`not` 只能用于单个标签（例如 `not slow`）。不支持括号。

### 示例

- `canify validate --tags "core"` (只运行带 `core` 标签的规则)
- `canify validate --tags "not slow"` (运行所有不带 `slow` 标签的规则)
- `canify validate --tags "core and service-management"` (同时拥有这两个标签的规则)
- `canify validate --tags "core or ui"` (拥有 `core` 或 `ui` 标签的规则)