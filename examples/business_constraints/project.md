---
title: "业务约束项目示例"
author: "项目经理"
created_at: "2025-10-17"
---

# 业务约束项目示例

这个项目展示了复杂的业务约束场景。

## 项目概述

[约束项目](entity://constraint-project) 是一个预算有限的项目，需要遵守严格的业务规则。

## 项目约束

1. **预算约束**: 任务总预算不能超过项目预算
2. **人员约束**: 任务负责人必须在项目团队中
3. **状态约束**: 已完成的任务不能重新激活

## 任务列表

- [核心功能开发](entity://task-core) - 预算 6000 元
- [用户界面设计](entity://task-ui) - 预算 3000 元
- [系统测试](entity://task-test) - 预算 2000 元

## 附录：实体定义

```entity
type: Project
id: constraint-project
name: 业务约束项目
budget: 10000.0
status: active
team_members: ["user-alice", "user-bob", "user-eve"]
```

```entity
type: Task
id: task-core
name: 核心功能开发
project_id: constraint-project
assignee: user-alice
budget: 6000.0
status: in-progress
```

```entity
type: Task
id: task-ui
name: 用户界面设计
project_id: constraint-project
assignee: user-bob
budget: 3000.0
status: in-progress
```

```entity
type: Task
id: task-test
name: 系统测试
project_id: constraint-project
assignee: user-eve
budget: 2000.0
status: in-progress
```