# 测试重复ID和schema验证

```entity
type: project
id: test-project
name: 测试项目
budget: "not_a_number"  # 类型错误
```

```entity
type: user
id: test-user
name: 测试用户
```

```entity
type: user
id: test-user  # 重复的实体ID
name: 另一个用户
```