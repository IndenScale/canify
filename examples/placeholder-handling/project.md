---
title: "占位符处理示例"
author: "项目团队"
created_at: "2025-10-17"
---

# 占位符处理示例

这个项目展示了 Canify 如何处理占位符，支持渐进式文档完善。

## 项目概述

[占位符项目](entity://placeholder-project) 是一个正在规划中的项目，很多细节尚未确定。

## 项目状态

- **预算**: 尚未确定
- **时间线**: 正在规划
- **团队规模**: 待确定

## 任务列表

- [需求收集](entity://task-requirements) - 进行中
- [技术选型](entity://task-technology) - 待开始
- [架构设计](entity://task-architecture) - 待开始

## 附录：实体定义

```entity
type: Project
id: placeholder-project
name: 占位符示例项目
budget: TBD
start_date: TODO
end_date: TBD
team_size: TBD
```

```entity
type: Task
id: task-requirements
name: 需求收集
project_id: placeholder-project
assignee: TBD
estimated_hours: 40.0
actual_hours: TBD
status: in-progress
```

```entity
type: Task
id: task-technology
name: 技术选型
project_id: placeholder-project
assignee: TODO
estimated_hours: TBD
actual_hours: TBD
status: in-progress
```

```entity
type: Task
id: task-architecture
name: 架构设计
project_id: placeholder-project
assignee: TBD
estimated_hours: 60.0
actual_hours: TBD
status: in-progress
```
