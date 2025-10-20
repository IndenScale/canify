# Canify 演示项目

这个演示项目展示了 Canify 工具的实际使用场景，包含自然行文的文档和结构化的实体定义。

## 设计理念

Canify 采用"文档即代码"的理念，但保持文档的自然可读性：

- **正常行文的文档**: 文档是自然的、可读的文本内容
- **实体声明在附录中**: 实体定义放在文档末尾的附录部分
- **引用语法链接**: 在文档正文中通过 `[链接文本](entity://ENTITY_ID)` 引用实体
- **Front Matter 用于文档元数据**: 描述整个文档的元信息

## 项目结构

```bash
demo/
├── project-planning.md      # 项目规划文档（包含项目和任务实体）
├── team-directory.md        # 团队人员文档（包含人员实体）
├── constraints/
│   └── business-rules.yaml  # 业务约束规则
└── models/
    └── __init__.py          # Pydantic 模型定义
```

## 实体概览

### 跨文档实体定义

- **项目规划文档** (`project-planning.md`) 包含：

  - **项目实体 (1 个)**: `canify-development`
  - **任务实体 (3 个)**: `task-001`, `task-002`, `task-003`

- **团队人员文档** (`team-directory.md`) 包含：
  - **用户实体 (4 个)**: `user-alice`, `user-bob`, `user-eve`, `user-charlie`

### 跨文档引用示例

在 `project-planning.md` 中：

```markdown-for-demo
本项目由 [Alice Zhang](entity://user-alice) 担任项目经理...
```

在 `team-directory.md` 中定义了对应的实体：

```entity-for-demo
type: User
id: user-alice
name: Alice Zhang
...
```

## 验证命令示例

### 基础验证

```bash
# Lax 模式验证 (允许占位符)
canify validate --mode=lax --path=demo

# Strict 模式验证 (禁止占位符)
canify validate --mode=strict --path=demo

# JSON 输出格式
canify validate --mode=lax --output=json --path=demo
```

### 查询功能

```bash
# 查询项目信息
canify query canify-development

# 查询特定字段
canify query canify-development --fields=name,budget,status

# 搜索任务
canify search "验证引擎" --type=task

# 搜索所有进行中的任务
canify search "in-progress" --type=task
```

### 缓存管理

```bash
# 重建缓存
canify cache rebuild --path=demo

# 清除缓存
canify cache clear
```

### 统计信息

```bash
# 项目统计
canify stats --path=demo
```

## 预期验证结果

### Lax 模式验证

在 Lax 模式下，验证应该通过，因为：

- 所有实体都有有效的 ID 和类型
- 实体引用关系正确
- 占位符 "TBD" 在 Lax 模式下被允许

### Strict 模式验证

在 Strict 模式下，验证会失败，因为：

- task-002 中的 `actual_hours: TBD` 占位符在 Strict 模式下不被允许
- 需要将占位符替换为实际值才能通过 Strict 验证

## 业务约束示例

演示项目中包含了以下两条核心业务约束规则：

1. **人员分配约束**: 任务负责人必须在项目开发人员列表中

   - 验证：`task.assignee in project.developers`
   - 示例：task-002 的负责人 user-bob 必须在 canify-development 的 developers 列表中

2. **状态依赖约束**: 活跃项目中的任务不能已完成
   - 验证：`project.status == 'active' => task.status != 'completed'`
   - 示例：canify-development 状态为 active，但 task-001 状态为 completed，会产生警告

## 占位符处理

演示项目展示了占位符的使用：

```yaml
# 在 Lax 模式下允许
actual_hours: TBD
```

这些占位符在 Lax 模式下会被跳过验证，但在 Strict 模式下会导致验证失败。

## 下一步

1. **实现 Canify 工具**: 根据架构设计实现四阶段验证引擎
2. **运行演示验证**: 使用 Canify 验证这个演示项目
3. **扩展实体类型**: 添加更多实体类型（如文档、里程碑等）
4. **自定义约束**: 根据具体业务需求添加更多约束规则

这个演示项目完整展示了 Canify 的核心概念和使用方式，可以作为实际项目的参考模板。

## 附录：演示实体定义

```entity
type: CanifyEntity
id: ENTITY_ID
name: 示例实体
```
