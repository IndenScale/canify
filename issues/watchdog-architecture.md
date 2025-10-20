# Watchdog 架构设计

issue_id: watchdog-architecture
type: architecture
status: design
priority: high
created: 2025-10-19
updated: 2025-10-19

## 概述

本文档详细设计 Canify Watchdog 系统的架构，包括 Canify Daemon、Observer 管理和文件变更检测机制。

## 核心架构

### 系统组件

```ascii
┌─────────────────┐   管理    ┌─────────────────┐
│  Canify Daemon  │──────────►│    Observers    │
│   (主守护进程)   │           │   (观察者进程)   │
└─────────────────┘           └─────────────────┘
         │                             │
         ▼                             ▼
┌─────────────────┐           ┌─────────────────┐
│  状态数据库     │           │  文件系统监听    │
│   (SQLite)      │           │  (inotify/fsevents) │
└─────────────────┘           └─────────────────┘
```

### 1. Canify Daemon (主守护进程)

**职责**:

- 管理所有 Observer 进程的生命周期
- 维护全局状态和配置
- 提供 CLI 接口用于管理 Observers
- 处理用户授权和权限管理

### 2. Observer (观察者进程)

**每个 Observer 监听一个逻辑根目录**，包含以下信息：

```python
class ObserverConfig:
    root_path: str              # 监听根目录的绝对路径
    status: str                 # "active" | "dormant"
    last_accessed: datetime     # 用户最后访问时间
    last_scanned: datetime      # 最后一次全量扫描时间
    ignore_file_path: Optional[str]  # 忽略文件路径（如 .canifyignore）
    created_at: datetime
    updated_at: datetime
```

## 数据库设计

### observers 表

```sql
CREATE TABLE observers (
    id INTEGER PRIMARY KEY,
    root_path TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'dormant')),
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ignore_file_path TEXT,  -- NULL 表示使用默认层级
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### current_files 表

```sql
CREATE TABLE current_files (
    id INTEGER PRIMARY KEY,
    observer_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,      -- 相对于根目录的路径
    last_modified TIMESTAMP NOT NULL,
    file_size INTEGER NOT NULL,
    content_hash TEXT NOT NULL,   -- 文件内容哈希
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observer_id) REFERENCES observers(id),
    UNIQUE(observer_id, file_path)
);
```

### state 表 (心跳记录)

```sql
CREATE TABLE state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 核心任务

### 任务 1: 文件变更检测和报告

**工作流程**:

```python
class Observer:
    def monitor_files(self):
        while self.running:
            # 实时监听文件系统事件
            events = self.file_watcher.poll()

            for event in events:
                if self.should_ignore_file(event.path):
                    continue

                if event.type == "modified":
                    self.handle_file_modified(event.path)
                elif event.type == "deleted":
                    self.handle_file_deleted(event.path)

            # 定期更新心跳
            if time.time() - self.last_heartbeat > 10:
                self.update_heartbeat()

    def handle_file_modified(self, file_path):
        # 计算文件哈希，与数据库比较
        current_hash = self.compute_file_hash(file_path)
        stored_hash = self.get_stored_hash(file_path)

        if current_hash != stored_hash:
            # 更新数据库
            self.update_file_record(file_path, current_hash)
            # 添加到变更列表
            self.updated_files.append(file_path)

    def handle_file_deleted(self, file_path):
        # 从数据库删除记录
        self.delete_file_record(file_path)
        # 添加到删除列表（带特殊标记）
        self.deleted_files.append(f"DELETED:{file_path}")
```

**变更报告格式**:

```python
class FileChanges:
    updated_files: List[str]        # 更新的文件路径
    deleted_files: List[str]        # 格式: "DELETED:/path/to/file"
    observer_id: int
    timestamp: datetime
```

### 任务 2: 启动时快速扫描

**工作流程**:

```python
def initial_scan(self):
    """Observer 启动时的全量扫描"""

    # 1. 扫描目录中的所有文件
    all_files = self.scan_directory(self.root_path)

    # 2. 过滤忽略文件
    filtered_files = self.filter_ignored_files(all_files)

    # 3. 快速检查：基于修改时间和文件大小
    for file_path in filtered_files:
        stat = os.stat(file_path)

        # 快速路径：检查修改时间和大小
        stored_record = self.get_file_record(file_path)
        if stored_record and self.is_quick_match(stored_record, stat):
            continue  # 文件未变化，跳过哈希计算

        # 慢速路径：计算内容哈希
        file_hash = self.compute_file_hash(file_path)

        if not stored_record or stored_record.content_hash != file_hash:
            # 文件有变化，更新数据库
            self.update_file_record(file_path, file_hash, stat)
            self.updated_files.append(file_path)

    # 4. 检测已删除的文件
    self.detect_deleted_files(filtered_files)

    # 5. 更新扫描时间
    self.update_last_scanned()
```

## 忽略文件层级

### 层级回避规则

当 `ignore_file_path` 为 NULL 时，遵循以下层级：

```bash
项目文件 (.canifyignore) > 用户配置 (~/.config/canify/ignore) > 系统配置 (/etc/canify/ignore) > 默认值
```

### 默认忽略模式

```python
DEFAULT_IGNORE_PATTERNS = [
    "*.tmp", "*.log", "*.swp", "*.bak",
    ".git/", ".svn/", ".hg/", ".bzr/",
    "node_modules/", "__pycache__/", ".pytest_cache/",
    "build/", "dist/", "*.egg-info/"
]
```

## 性能优化

### 1. 心跳机制

```python
def update_heartbeat(self):
    """每10秒更新一次心跳记录"""
    with self.db_connection:
        self.db_connection.execute(
            "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
            (f"observer_{self.id}_heartbeat", datetime.now().isoformat())
        )
    self.last_heartbeat = time.time()
```

### 2. 快速变更检测

```python
def is_quick_match(self, stored_record, current_stat):
    """快速检查文件是否变化（避免哈希计算）"""
    return (
        stored_record.last_modified == current_stat.st_mtime and
        stored_record.file_size == current_stat.st_size
    )
```

### 3. 休眠模式优化

```python
def manage_observer_state(self):
    """根据访问频率管理 Observer 状态"""

    # 长时间未访问的 Observer 进入休眠模式
    inactive_time = datetime.now() - self.last_accessed
    if inactive_time > timedelta(days=7):
        self.status = "dormant"
        self.stop_monitoring()
    else:
        self.status = "active"
        self.start_monitoring()
```

## CLI 管理接口

### 命令示例

```bash
# 启动监听目录
canify watch add /path/to/project --ignore .canifyignore

# 查看所有监听目录
canify watch list

# 停止监听目录
canify watch stop /path/to/project

# 删除监听目录
canify watch remove /path/to/project

# 手动触发扫描
canify watch scan /path/to/project
```

## 待办事项

- [ ] 实现 Canify Daemon 进程管理
- [ ] 实现 Observer 生命周期管理
- [ ] 设计 Observer-CLI 通信协议
- [ ] 实现忽略文件层级系统
- [ ] 优化大目录扫描性能
- [ ] 实现休眠模式状态转换
- [ ] 设计错误恢复机制

## 相关文档

- [Canify Standalone 设计](../issues/canify-standalone-design.yaml)
- [产品计划书](../docs/PRODUCT_PLAN.md)
