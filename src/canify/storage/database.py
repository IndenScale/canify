"""
Canify 数据库管理模块

负责SQLite数据库的初始化、连接管理和模式创建。
"""

import sqlite3
import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 默认数据库路径：用户主目录下的 .canify/canify.db
            home_dir = Path.home()
            self.db_path = home_dir / ".canify" / "canify.db"
        else:
            self.db_path = db_path

        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用线程本地存储，每个线程有自己的连接
        self._local = threading.local()

    def connect(self) -> sqlite3.Connection:
        """
        连接到数据库，如果不存在则创建
        使用线程本地存储，确保每个线程有自己的连接

        Returns:
            SQLite连接对象
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row

            # 启用外键约束
            self._local.connection.execute("PRAGMA foreign_keys = ON")

            # 启用WAL模式提高并发性能
            self._local.connection.execute("PRAGMA journal_mode = WAL")

            logger.debug(f"线程 {threading.current_thread().name} 连接到数据库: {self.db_path}")

        return self._local.connection

    def initialize_schema(self) -> None:
        """初始化数据库模式"""
        conn = self.connect()

        try:
            # 创建项目元数据表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_path TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建文件状态表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    last_modified TIMESTAMP NOT NULL,
                    parsed_at TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE(project_id, file_path)
                )
            """)

            # 创建实体声明表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_declarations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    file_id INTEGER NOT NULL,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    raw_data TEXT NOT NULL,
                    source_code TEXT NOT NULL,
                    location_file TEXT NOT NULL,
                    location_line INTEGER NOT NULL,
                    location_column INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                    UNIQUE(project_id, entity_id)
                )
            """)

            # 创建实体引用表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    file_id INTEGER NOT NULL,
                    source_entity_id TEXT,
                    target_entity_id TEXT NOT NULL,
                    reference_text TEXT NOT NULL,
                    location_file TEXT NOT NULL,
                    location_line INTEGER NOT NULL,
                    location_column INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                )
            """)

            # 创建符号依赖关系表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbol_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    dependent_file_id INTEGER NOT NULL,
                    depended_symbol_type TEXT NOT NULL,
                    depended_symbol_id TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (dependent_file_id) REFERENCES files(id) ON DELETE CASCADE
                )
            """)

            # 创建实体模式表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_schemas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    file_id INTEGER NOT NULL,
                    schema_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    schema_data TEXT NOT NULL,
                    source_code TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                    UNIQUE(project_id, schema_name)
                )
            """)

            # 创建 spec 规则表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spec_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    file_id INTEGER NOT NULL,
                    rule_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    env TEXT NOT NULL DEFAULT 'local',
                    fixture TEXT,
                    test_case TEXT,
                    levels TEXT NOT NULL, -- JSON 格式存储
                    tags TEXT, -- JSON 格式存储
                    source_code TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                    UNIQUE(project_id, rule_id)
                )
            """)

            # 创建索引
            self._create_indexes(conn)

            conn.commit()
            logger.info("数据库模式初始化完成")

        except Exception as e:
            conn.rollback()
            logger.error(f"数据库模式初始化失败: {e}")
            raise

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """创建数据库索引"""

        # 文件相关索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_project_path ON files(project_id, file_path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)")

        # 实体声明索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_project ON entity_declarations(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_file ON entity_declarations(file_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_id ON entity_declarations(entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entity_declarations(entity_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_location ON entity_declarations(location_file, location_line)")

        # 实体引用索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_references_project ON entity_references(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_references_file ON entity_references(file_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_references_source ON entity_references(source_entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_references_target ON entity_references(target_entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_references_location ON entity_references(location_file, location_line)")

        # 依赖关系索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dependencies_file ON symbol_dependencies(dependent_file_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dependencies_symbol ON symbol_dependencies(depended_symbol_type, depended_symbol_id)")

        # 实体模式索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_schemas_project ON entity_schemas(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_schemas_file ON entity_schemas(file_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_schemas_name ON entity_schemas(schema_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_schemas_type ON entity_schemas(entity_type)")

        # spec 规则索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spec_rules_project ON spec_rules(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spec_rules_file ON spec_rules(file_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spec_rules_id ON spec_rules(rule_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spec_rules_env ON spec_rules(env)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spec_rules_tags ON spec_rules(tags)")

    def close(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug(f"线程 {threading.current_thread().name} 数据库连接已关闭")

    def close_all_threads(self) -> None:
        """关闭所有线程的数据库连接（用于主线程清理）"""
        # 注意：这个方法只能关闭当前线程的连接
        # 在多线程环境中，每个线程应该自己管理连接的关闭
        self.close()

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def vacuum(self) -> None:
        """执行数据库整理，回收空间"""
        conn = self.connect()
        conn.execute("VACUUM")
        conn.commit()
        logger.info("数据库整理完成")


def get_database_manager(db_path: Optional[Path] = None) -> DatabaseManager:
    """
    获取数据库管理器实例

    Args:
        db_path: 数据库文件路径

    Returns:
        数据库管理器实例
    """
    return DatabaseManager(db_path)