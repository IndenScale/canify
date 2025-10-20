# Issues 目录

这个目录用于记录 Canify 项目的架构讨论、设计决策和问题跟踪。

## 文件格式

所有问题记录使用 YAML 格式，包含以下标准字段：

```yaml
issue_id: "唯一标识符"
title: "问题标题"
status: "状态 (discussed/resolved/pending)"
priority: "优先级 (high/medium/low)"
created_at: "创建日期"
updated_at: "最后更新日期"
participants: ["参与者列表"]
background: "问题背景描述"
# ... 其他相关字段
```

## 当前问题记录

### 架构讨论

- [architecture-discussion.yaml](./architecture-discussion.yaml) - Canify 状态化服务器架构设计讨论

### 特性演进记录

- [fixture-test-case-decorators.yaml](./fixture-test-case-decorators.yaml) - Fixture 和 Test Case 装饰器系统
- [fixture-test-case-type-system.yaml](./fixture-test-case-type-system.yaml) - Fixture 和 Test Case 类型化系统
- [watchdog-file-watching.yaml](./watchdog-file-watching.yaml) - Watchdog 文件监听和增量扫描
- [gitignore-support.yaml](./gitignore-support.yaml) - Gitignore 支持和独立 Canifyignore 文件
- [branch-checkpoint-views.yaml](./branch-checkpoint-views.yaml) - 分支视图和检查点视图分离

## 使用指南

1. **创建新问题**：使用 YAML 格式记录新的架构讨论或问题
2. **更新状态**：当问题有进展时更新状态字段
3. **记录决策**：重要的设计决策应该记录在相关文件中
4. **关联文档**：在 `related_files` 字段中关联相关文档

## 最佳实践

- 保持 YAML 文件的结构清晰和一致性
- 使用描述性的 issue_id 便于查找
- 及时更新问题状态
- 记录所有参与者的贡献
