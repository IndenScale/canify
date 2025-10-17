---
title: "测试文档"
author: "测试人员"
---

# 测试文档

这是一个包含实体声明和引用的测试文档。

## 项目信息

本项目由 [Alice](entity://user-alice) 负责管理，包含以下任务：

- [需求分析](entity://task-001) - 由 [Bob](entity://user-bob) 负责
- [架构设计](entity://task-002) - 由 [Charlie](entity://user-charlie) 负责

## 项目状态

当前项目处于 **活跃** 状态，预计在年底完成。

## 附录：实体定义

```entity
type: project
id: test-project
name: 测试项目
budget: 10000.0
status: active
```

```entity
type: user
id: user-alice
name: Alice Zhang
email: alice@example.com
role: project-manager
```

```entity
type: user
id: user-bob
name: Bob Li
email: bob@example.com
role: developer
```

```entity
type: task
id: task-001
name: 需求分析
project_id: test-project
assignee: user-bob
status: completed
```

```entity
type: task
id: task-002
name: 架构设计
project_id: test-project
assignee: user-charlie
status: in-progress
```