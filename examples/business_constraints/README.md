# 业务约束示例

这个示例展示了 Canify 的业务约束功能，包括复杂的业务规则验证。

## 示例内容

- 预算分配约束
- 人员角色约束
- 状态依赖约束
- 时间线约束

## 验证命令

```bash
# 基础验证（可能通过）
canify verify examples/business-constraints

# 严格验证（可能失败，展示约束违反）
canify validate examples/business-constraints
```

## 预期行为

在严格模式下，验证会失败并显示具体的业务约束违反信息。