---
title: "项目文档"
author: "项目管理"
created_at: "2025-10-17"
---

# 项目文档

这个文档包含多个项目实体的定义。

## 项目列表

### 核心项目

- [Canify 开发](entity://project-canify) - 主要开发项目
- [文档系统](entity://project-docs) - 文档管理系统

### 支持项目

- [测试框架](entity://project-testing) - 测试基础设施
- [部署系统](entity://project-deployment) - 部署工具链

## 项目关系

这些项目之间存在复杂的依赖关系：

- [Canify 开发](entity://project-canify) 依赖 [测试框架](entity://project-testing)
- [文档系统](entity://project-docs) 依赖 [Canify 开发](entity://project-canify)
- [部署系统](entity://project-deployment) 依赖所有其他项目

## 附录：项目实体定义

```entity
type: Project
id: project-canify
name: Canify 开发项目
budget: 50000.0
status: active
dependencies: ["project-testing"]
```

```entity
type: Project
id: project-docs
name: 文档系统项目
budget: 20000.0
status: active
dependencies: ["project-canify"]
```

```entity
type: Project
id: project-testing
name: 测试框架项目
budget: 15000.0
status: active
dependencies: []
```

```entity
type: Project
id: project-deployment
name: 部署系统项目
budget: 25000.0
status: active
dependencies: ["project-canify", "project-docs", "project-testing"]
```