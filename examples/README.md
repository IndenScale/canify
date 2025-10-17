# Canify 示例项目

这个目录包含精心设计的 Canify 演示项目，每个示例专注于一个核心概念。

## 示例概览

### 1. 基础概念示例 (`basic-concepts/`)

**目标**: 展示 Canify 的核心概念和基本功能

- 简单的项目、任务、用户实体
- 基本的实体引用
- 必需字段验证
- 类型验证

**验证命令**:
```bash
canify verify examples/basic-concepts
canify validate examples/basic-concepts
canify lint examples/basic-concepts
```

### 2. 业务约束示例 (`business-constraints/`)

**目标**: 展示复杂的业务规则验证

- 预算分配约束
- 团队成员分配约束
- 状态一致性约束
- 自定义业务规则

**验证命令**:
```bash
canify verify examples/business-constraints
canify validate examples/business-constraints
```

**预期行为**:
- 在 `verify` 模式下显示预算超支警告
- 在 `validate` 模式下预算超支被视为错误

### 3. 占位符处理示例 (`placeholder-handling/`)

**目标**: 展示占位符处理功能

- 使用占位符 "TBD"、"TODO"
- Lax 模式和 Strict 模式的对比
- 渐进式文档完善

**验证命令**:
```bash
canify verify examples/placeholder-handling
canify validate examples/placeholder-handling
```

**预期行为**:
- 在 Lax 模式下允许占位符
- 在 Strict 模式下禁止占位符

### 4. 跨文档引用示例 (`cross-document-references/`)

**目标**: 展示复杂的跨文档引用网络

- 多个文档间的实体引用
- 复杂的引用关系网络
- 项目依赖关系
- 任务依赖关系

**验证命令**:
```bash
canify verify examples/cross-document-references
canify validate examples/cross-document-references
```

## 演示场景

### 开发工作流集成

1. **编辑阶段**: 使用 `canify lint` 进行快速检查
2. **提交阶段**: 使用 `canify verify` 确保结构完整性
3. **合并阶段**: 使用 `canify validate` 执行严格验证

### 质量门示例

```bash
# 编辑时快速检查
canify lint examples/basic-concepts

# 提交时结构验证
canify verify examples/business-constraints

# 合并时业务规则验证
canify validate examples/business-constraints
```

## 技术特点展示

### 实体类型
- **项目 (project)**: 包含预算、状态、团队信息
- **任务 (task)**: 包含负责人、时间估算、状态
- **用户 (user)**: 包含角色、技能、联系信息

### 验证功能
- **符号发现**: 重复实体ID检测
- **引用验证**: 悬空引用检测
- **类型验证**: 字段类型检查
- **业务规则**: 自定义约束验证

### 占位符支持
- **TBD**: 待确定
- **TODO**: 待完成
- Lax 模式允许占位符
- Strict 模式禁止占位符

## 使用建议

1. **新用户**: 从 `basic-concepts/` 开始，了解核心概念
2. **进阶用户**: 查看 `business-constraints/` 了解业务规则
3. **团队协作**: 参考 `cross-document-references/` 了解复杂引用
4. **渐进开发**: 使用 `placeholder-handling/` 了解占位符处理

这些示例项目完整展示了 Canify 的强大功能，可以作为实际项目的参考模板。