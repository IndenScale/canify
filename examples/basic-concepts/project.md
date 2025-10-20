---
title: "基础项目示例"
author: "示例作者"
created_at: "2025-10-17"
---

# 基础项目示例

这是一个简单的项目示例，展示了 Canify 的基本功能。

## 项目概述

本项目 [示例项目](entity://basic-project) 是一个演示项目，包含几个简单的任务。

## 任务列表

- [需求分析](entity://task-analysis) - 已完成
- [架构设计](entity://task-design) - 进行中
- [测试实施](entity://task-testing) - 待开始

## 项目状态

项目目前处于 **活跃** 状态，预计在 2025 年底完成。

## 附录：实体定义

```entity
type: Project
id: basic-project
name: 基础示例项目
budget: 10000.0
status: active
manager: user-alice
```

```entity
type: Task
id: task-analysis
name: 需求分析
project_id: basic-project
assignee: user-alice
estimated_hours: 20.0
actual_hours: 18.5
status: completed
```

```entity
type: Task
id: task-design
name: 架构设计
project_id: basic-project
assignee: user-bob
estimated_hours: 40.0
actual_hours: 25.0
status: in-progress
```

```entity
type: Task
id: task-testing
name: 测试实施
project_id: basic-project
assignee: user-charlie
estimated_hours: 30.0
actual_hours: 0.0
status: in-progress
```
