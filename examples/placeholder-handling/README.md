# 占位符处理示例

这个示例展示了 Canify 的占位符处理功能，包括 Lax 和 Strict 模式的区别。

## 示例内容

- 使用占位符 "TBD" 的实体
- 使用占位符 "TODO" 的实体
- 使用占位符 "?" 的实体
- Lax 模式和 Strict 模式的对比

## 验证命令

```bash
# Lax 模式验证（允许占位符）
canify verify examples/placeholder-handling

# Strict 模式验证（禁止占位符）
canify validate examples/placeholder-handling
```

## 预期行为

- **Lax 模式**: 验证通过，占位符被允许
- **Strict 模式**: 验证失败，显示占位符错误