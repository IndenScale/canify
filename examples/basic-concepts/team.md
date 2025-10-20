---
title: "团队人员示例"
author: "HR Department"
created_at: "2025-10-17"
---

# 团队人员示例

这个文档展示了团队人员实体的定义。

## 团队成员

### 管理团队

- **[Alice Zhang](entity://user-alice)** - 项目经理
- **[Eve Wang](entity://user-eve)** - 产品经理

### 技术团队

- **[Bob Li](entity://user-bob)** - 后端工程师
- **[Charlie Chen](entity://user-charlie)** - 前端工程师

## 团队协作

团队成员通过 Canify 实体引用进行协作，确保文档间的关联性。

## 附录：人员实体定义

```entity
type: User
id: user-alice
name: Alice Zhang
email: alice@example.com
role: project-manager
skills: ["project-management", "agile", "documentation"]
```

```entity
type: User
id: user-bob
name: Bob Li
email: bob@example.com
role: backend-developer
skills: ["python", "sqlite", "system-design"]
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
id: user-charlie
name: Charlie Chen
email: charlie@example.com
role: frontend-developer
skills: ["react", "typescript", "ui-design"]
```
