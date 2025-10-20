---
title: "团队文档"
author: "人力资源"
created_at: "2025-10-17"
---

# 团队文档

这个文档包含团队成员的定义，被其他文档引用。

## 团队成员

### 核心开发团队

- **[Alice Zhang](entity://user-alice)** - 技术负责人
- **[Bob Li](entity://user-bob)** - 后端工程师
- **[Charlie Chen](entity://user-charlie)** - 前端工程师

### 产品团队

- **[Eve Wang](entity://user-eve)** - 产品经理
- **[David Liu](entity://user-david)** - UX设计师

### 质量保证

- **[Fiona Yang](entity://user-fiona)** - 测试工程师
- **[George Wu](entity://user-george)** - DevOps工程师

## 团队协作

团队成员分布在不同的项目中，通过实体引用建立关联：

- [Alice Zhang](entity://user-alice) 负责 [验证引擎开发](entity://task-validation)
- [Bob Li](entity://user-bob) 负责 [缓存系统实现](entity://task-cache)
- [Charlie Chen](entity://user-charlie) 负责 [CLI 接口设计](entity://task-cli)

## 附录：人员实体定义

```entity
type: User
id: user-alice
name: Alice Zhang
email: alice@example.com
role: tech-lead
skills: ["python", "system-design", "architecture"]
```

```entity
type: User
id: user-bob
name: Bob Li
email: bob@example.com
role: backend-developer
skills: ["python", "sqlite", "performance"]
```

```entity
type: User
id: user-charlie
name: Charlie Chen
email: charlie@example.com
role: frontend-developer
skills: ["react", "typescript", "ui-design"]
```

```entity
type: User
id: user-eve
name: Eve Wang
email: eve@example.com
role: product-manager
skills: ["product-planning", "user-research"]
```

```entity
type: User
id: user-david
name: David Liu
email: david@example.com
role: ux-designer
skills: ["ui-design", "user-testing", "prototyping"]
```

```entity
type: User
id: user-fiona
name: Fiona Yang
email: fiona@example.com
role: test-engineer
skills: ["testing", "qa", "automation"]
```

```entity
type: User
id: user-george
name: George Wu
email: george@example.com
role: devops-engineer
skills: ["deployment", "infrastructure", "monitoring"]
```