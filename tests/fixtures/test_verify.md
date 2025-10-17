# 测试验证功能

这个文件包含一些有问题的实体声明和引用，用于测试 verify 命令。

## 实体声明

```entity
type: project
id: test-project
name: 测试项目
budget: "not_a_number"  # 这里应该是数字
status: invalid_status  # 无效的状态值
```

```entity
type: user
id: test-user
name: 测试用户
email: test@example.com
```

```entity
type: user
id: test-user  # 重复的实体ID
name: 另一个用户
```

## 实体引用

这里引用了一个不存在的实体：[不存在的实体](entity://non-existent-entity)

这里引用了一个存在的实体：[测试用户](entity://test-user)