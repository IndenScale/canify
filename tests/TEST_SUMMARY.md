# Canify 测试总结

## 测试覆盖范围

本项目为 Canify 实现了全面的测试套件，覆盖了所有核心功能模块。

### 1. 核心模型测试 (`tests/unit/models/`)

- **`test_entity_declaration.py`**: 实体声明模型测试
  - 实体创建和验证
  - 字符串表示
  - 复杂数据处理
  - 必需字段验证

- **`test_entity_reference.py`**: 实体引用模型测试
  - 引用创建和验证
  - 特殊字符处理
  - Unicode 字符支持
  - 上下文文本处理

- **`test_symbol_table.py`**: 符号表模型测试
  - 实体添加和查找
  - 引用管理
  - 类型分组
  - 重复ID处理

- **`test_validation_result.py`**: 验证结果模型测试
  - 错误和警告管理
  - 问题总数计算
  - 位置信息格式化

### 2. 解析器测试 (`tests/unit/parsers/`)

- **`test_entity_declaration_parser.py`**: 实体声明解析器测试
  - 有效实体解析
  - 无效YAML处理
  - 位置信息计算
  - 复杂数据结构解析

- **`test_entity_reference_parser.py`**: 实体引用解析器测试
  - 有效引用解析
  - 特殊字符处理
  - 位置信息计算
  - 上下文文本提取

### 3. 验证引擎测试 (`tests/unit/validation/`)

- **`test_validation_engine.py`**: 验证引擎测试
  - 符号发现阶段
  - 引用验证阶段
  - 数据模型校验
  - 业务规则验证
  - 错误检测和处理

### 4. 异常体系测试 (`tests/unit/exceptions/`)

- **`test_exceptions.py`**: 异常类测试
  - 基础验证错误
  - 具体异常类型
  - 错误消息格式化
  - 继承层次验证

### 5. 集成测试 (`tests/integration/`)

- **`test_cli_commands.py`**: CLI 命令集成测试
  - lint 命令测试
  - verify 命令测试
  - validate 命令测试
  - 错误处理测试
  - 详细模式测试

- **`test_end_to_end.py`**: 端到端测试
  - 有效项目验证
  - 无效项目检测
  - 复杂引用网络
  - 性能测试
  - 多种验证模式

## 测试策略

### 单元测试
- 针对每个独立模块进行测试
- 使用模拟数据和依赖注入
- 覆盖边界条件和错误情况

### 集成测试
- 测试模块间的交互
- 使用真实文件和目录结构
- 验证端到端工作流程

### 性能测试
- 验证大规模数据处理能力
- 确保响应时间符合要求
- 测试内存使用情况

## 测试数据

### 测试夹具
- `tests/fixtures/`: 包含各种测试用例的 Markdown 文件
- 临时文件和目录: 在运行时动态创建

### 测试用例分类
1. **正向测试**: 验证正常功能
2. **负向测试**: 验证错误处理
3. **边界测试**: 验证边界条件
4. **性能测试**: 验证系统性能

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定类型的测试
```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 运行特定模块的测试
pytest tests/unit/models/
```

### 生成测试报告
```bash
# 生成 HTML 报告
pytest --html=report.html

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 测试覆盖率目标

- **行覆盖率**: > 90%
- **分支覆盖率**: > 85%
- **功能覆盖率**: 100%

## 持续集成

测试套件设计为可在 CI/CD 环境中运行，包括：
- GitHub Actions
- GitLab CI
- Jenkins
- 其他 CI 系统

## 测试维护

- 定期更新测试用例以适应代码变更
- 添加新功能的测试用例
- 重构测试代码以提高可维护性
- 监控测试执行时间和性能