# 跨文档引用示例

这个示例展示了 Canify 的跨文档引用功能，包括复杂的实体引用网络。

## 示例内容

- 多个文档间的实体引用
- 复杂的引用关系网络
- 循环依赖检测
- 悬空引用检测

## 验证命令

```bash
# 基础验证
canify verify examples/cross-document-references

# 严格验证
canify validate examples/cross-document-references
```

## 预期行为

验证会检查跨文档的引用关系，确保所有引用都是有效的。