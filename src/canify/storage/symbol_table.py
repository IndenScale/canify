"""
符号表管理器

负责符号表的持久化存储、查询和增量更新。
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sqlite3

from ..models import EntityDeclaration, EntityReference, Location
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class SymbolTableManager:
    """符号表管理器"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化符号表管理器

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager

    def get_or_create_project(self, project_path: Path) -> int:
        """
        获取或创建项目记录

        Args:
            project_path: 项目根目录绝对路径

        Returns:
            项目ID
        """
        conn = self.db_manager.connect()

        # 尝试获取现有项目
        cursor = conn.execute(
            "SELECT id FROM projects WHERE project_path = ?",
            (str(project_path.absolute()),)
        )
        result = cursor.fetchone()

        if result:
            return result["id"]

        # 创建新项目
        cursor = conn.execute(
            "INSERT INTO projects (project_path) VALUES (?)",
            (str(project_path.absolute()),)
        )
        conn.commit()

        logger.info("创建项目记录: %s", project_path)
        return cursor.lastrowid  # type: ignore

    def clear_project_data(self, project_id: int) -> None:
        """
        清除指定项目的所有数据，用于冷启动。

        Args:
            project_id: 项目ID
        """
        conn = self.db_manager.connect()
        try:
            logger.warning(f"正在清除项目ID {project_id} 的所有数据...")
            conn.execute("DELETE FROM entity_declarations WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM entity_references WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM entity_schemas WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM files WHERE project_id = ?", (project_id,))
            # 注意：spec_definitions 和 symbol_dependencies 也可能需要清理
            # conn.execute("DELETE FROM spec_definitions WHERE project_id = ?", (project_id,))
            # conn.execute("DELETE FROM symbol_dependencies WHERE project_id = ?", (project_id,))
            conn.commit()
            logger.info(f"项目ID {project_id} 的数据已清除。")
        except Exception as e:
            conn.rollback()
            logger.error(f"清除项目数据失败: {e}")
            raise

    def get_file_record(self, project_id: int, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件记录

        Args:
            project_id: 项目ID
            file_path: 文件路径（相对于项目根目录）

        Returns:
            文件记录字典，如果不存在则返回None
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT id, file_path, file_hash, last_modified, parsed_at, status, error_message
            FROM files
            WHERE project_id = ? AND file_path = ?
            """,
            (project_id, file_path)
        )

        result = cursor.fetchone()
        return dict(result) if result else None

    def update_file_status(self, project_id: int, file_path: str, status: str, error_message: Optional[str] = None) -> None:
        """
        更新文件的状态和错误信息。

        Args:
            project_id: 项目ID
            file_path: 文件路径
            status: 新的状态 (e.g., 'error', 'parsed')
            error_message: 相关的错误信息
        """
        conn = self.db_manager.connect()
        try:
            conn.execute(
                """
                UPDATE files 
                SET status = ?, error_message = ?, parsed_at = ?
                WHERE project_id = ? AND file_path = ?
                """,
                (status, error_message, datetime.now().isoformat(), project_id, file_path)
            )
            conn.commit()
            logger.info(f"文件状态已更新: {file_path} -> {status}")
        except Exception as e:
            conn.rollback()
            logger.error(f"更新文件状态失败: {e}")
            raise

    def calculate_file_hash(self, content: str) -> str:
        """
        计算文件内容哈希

        Args:
            content: 文件内容

        Returns:
            文件哈希值
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def delete_symbols_by_file(self, project_id: int, file_path: str) -> None:
        """
        删除指定文件的所有相关符号

        Args:
            project_id: 项目ID
            file_path: 文件路径
        """
        conn = self.db_manager.connect()

        try:
            # 获取文件ID
            cursor = conn.execute(
                "SELECT id FROM files WHERE project_id = ? AND file_path = ?",
                (project_id, file_path)
            )
            file_record = cursor.fetchone()

            if not file_record:
                return

            file_id = file_record["id"]

            # 删除依赖关系
            conn.execute(
                "DELETE FROM symbol_dependencies WHERE dependent_file_id = ?",
                (file_id,)
            )

            # 删除实体引用
            conn.execute(
                "DELETE FROM entity_references WHERE file_id = ?",
                (file_id,)
            )

            # 删除实体声明
            conn.execute(
                "DELETE FROM entity_declarations WHERE file_id = ?",
                (file_id,)
            )

            # 更新文件状态
            conn.execute(
                "UPDATE files SET status = 'pending', parsed_at = NULL WHERE id = ?",
                (file_id,)
            )

            conn.commit()
            logger.debug(f"删除文件 {file_path} 的所有符号")

        except Exception as e:
            conn.rollback()
            logger.error(f"删除文件符号失败: {e}")
            raise

    def insert_symbols(
        self,
        project_id: int,
        file_path: str,
        declarations: List[EntityDeclaration],
        references: List[EntityReference]
    ) -> None:
        """
        插入符号到数据库

        Args:
            project_id: 项目ID
            file_path: 文件路径
            declarations: 实体声明列表
            references: 实体引用列表
        """
        conn = self.db_manager.connect()

        try:
            # 获取或创建文件记录
            file_record = self.get_file_record(project_id, file_path)
            if file_record:
                file_id = file_record["id"]
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO files (project_id, file_path, file_hash, last_modified, status)
                    VALUES (?, ?, ?, ?, 'parsing')
                    """,
                    (project_id, file_path, "", datetime.now().isoformat())
                )
                file_id = cursor.lastrowid

            # 插入实体声明
            for declaration in declarations:
                conn.execute(
                    """
                    INSERT INTO entity_declarations (
                        project_id, file_id, entity_id, entity_type, name,
                        raw_data, source_code, location_file, location_line, location_column
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id, file_id, declaration.entity_id, declaration.entity_type,
                        declaration.name, json.dumps(declaration.raw_data, ensure_ascii=False),
                        declaration.source_code, str(declaration.location.file_path),
                        declaration.location.start_line, declaration.location.start_column or 1
                    )
                )

            # 插入实体引用
            for reference in references:
                conn.execute(
                    """
                    INSERT INTO entity_references (
                        project_id, file_id, source_entity_id, target_entity_id,
                        reference_text, location_file, location_line, location_column
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id, file_id, reference.source_entity_id,
                        reference.target_entity_id, reference.context_text,
                        str(reference.location.file_path), reference.location.start_line,
                        reference.location.start_column or 1
                    )
                )

            # 更新文件状态
            conn.execute(
                "UPDATE files SET status = 'parsed', parsed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), file_id)
            )

            conn.commit()
            logger.debug(f"插入 {len(declarations)} 个实体声明和 {len(references)} 个实体引用到文件 {file_path}")

        except Exception as e:
            conn.rollback()
            logger.error(f"插入符号失败: {e}")
            raise

    def get_entity_by_id(self, project_id: int, entity_id: str) -> Optional[EntityDeclaration]:
        """
        根据实体ID获取实体声明

        Args:
            project_id: 项目ID
            entity_id: 实体ID

        Returns:
            实体声明对象，如果不存在则返回None
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT entity_id, entity_type, name, raw_data, source_code,
                   location_file, location_line, location_column
            FROM entity_declarations
            WHERE project_id = ? AND entity_id = ?
            """,
            (project_id, entity_id)
        )

        result = cursor.fetchone()
        if not result:
            return None

        return self._row_to_entity_declaration(result)

    def get_entities_by_type(self, project_id: int, entity_type: str) -> List[EntityDeclaration]:
        """
        根据实体类型获取实体声明列表

        Args:
            project_id: 项目ID
            entity_type: 实体类型

        Returns:
            实体声明列表
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT entity_id, entity_type, name, raw_data, source_code,
                   location_file, location_line, location_column
            FROM entity_declarations
            WHERE project_id = ? AND entity_type = ?
            """,
            (project_id, entity_type)
        )

        return [self._row_to_entity_declaration(row) for row in cursor.fetchall()]

    def get_all_entities(self, project_id: int) -> List[EntityDeclaration]:
        """
        获取项目中的所有实体声明

        Args:
            project_id: 项目ID

        Returns:
            实体声明列表
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT entity_id, entity_type, name, raw_data, source_code,
                   location_file, location_line, location_column
            FROM entity_declarations
            WHERE project_id = ?
            """,
            (project_id,)
        )

        return [self._row_to_entity_declaration(row) for row in cursor.fetchall()]

    def get_all_symbols(self, project_id: int) -> List[EntityDeclaration]:
        """
        获取项目中的所有符号（目前实现为所有实体声明）。
        这是一个用于未来扩展的接口。
        """
        return self.get_all_entities(project_id)

    def get_references_by_target(self, project_id: int, target_entity_id: str) -> List[EntityReference]:
        """
        获取引用特定实体的所有引用

        Args:
            project_id: 项目ID
            target_entity_id: 目标实体ID

        Returns:
            实体引用列表
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT source_entity_id, target_entity_id, reference_text,
                   location_file, location_line, location_column
            FROM entity_references
            WHERE project_id = ? AND target_entity_id = ?
            """,
            (project_id, target_entity_id)
        )

        return [self._row_to_entity_reference(row) for row in cursor.fetchall()]

    def get_all_references(self, project_id: int) -> List[EntityReference]:
        """
        获取项目中的所有引用

        Args:
            project_id: 项目ID

        Returns:
            实体引用列表
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT source_entity_id, target_entity_id, reference_text,
                   location_file, location_line, location_column
            FROM entity_references
            WHERE project_id = ?
            """,
            (project_id,)
        )

        return [self._row_to_entity_reference(row) for row in cursor.fetchall()]

    def get_dangling_references(self, project_id: int) -> List[EntityReference]:
        """
        获取所有悬空引用（引用了不存在的实体）

        Args:
            project_id: 项目ID

        Returns:
            悬空引用列表
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT er.source_entity_id, er.target_entity_id, er.reference_text,
                   er.location_file, er.location_line, er.location_column
            FROM entity_references er
            LEFT JOIN entity_declarations ed ON er.target_entity_id = ed.entity_id AND er.project_id = ed.project_id
            WHERE er.project_id = ? AND ed.id IS NULL
            """,
            (project_id,)
        )

        return [self._row_to_entity_reference(row) for row in cursor.fetchall()]

    def insert_schema(self, project_id: int, file_path: str, schema_data: Dict[str, Any]) -> None:
        """
        插入实体模式到数据库

        Args:
            project_id: 项目ID
            file_path: 文件路径
            schema_data: 模式数据字典
        """
        conn = self.db_manager.connect()

        try:
            # 获取或创建文件记录
            file_record = self.get_file_record(project_id, file_path)
            if file_record:
                file_id = file_record["id"]
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO files (project_id, file_path, file_hash, last_modified, status)
                    VALUES (?, ?, ?, ?, 'parsing')
                    """,
                    (project_id, file_path, "", datetime.now().isoformat())
                )
                file_id = cursor.lastrowid

            # 插入实体模式
            conn.execute(
                """
                INSERT OR REPLACE INTO entity_schemas (
                    project_id, file_id, schema_name, entity_type,
                    schema_data, source_code, file_path, line_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, file_id, schema_data["name"], schema_data["name"],  # entity_type 使用 schema_name (首字母大写)
                    json.dumps(schema_data, ensure_ascii=False), schema_data.get("source_code", ""),
                    schema_data["file_path"], schema_data["line_number"]
                )
            )

            conn.commit()
            logger.debug(f"插入实体模式: {schema_data['name']}")

        except Exception as e:
            conn.rollback()
            logger.error(f"插入实体模式失败: {e}")
            raise

    def get_schema_by_name(self, project_id: int, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        根据模式名称获取实体模式

        Args:
            project_id: 项目ID
            schema_name: 模式名称

        Returns:
            模式数据字典，如果不存在则返回None
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT schema_data FROM entity_schemas
            WHERE project_id = ? AND schema_name = ?
            """,
            (project_id, schema_name)
        )

        result = cursor.fetchone()
        if not result:
            return None

        return json.loads(result["schema_data"])

    def get_schema_by_entity_type(self, project_id: int, entity_type: str) -> Optional[Dict[str, Any]]:
        """
        根据实体类型获取实体模式

        Args:
            project_id: 项目ID
            entity_type: 实体类型

        Returns:
            模式数据字典，如果不存在则返回None
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT schema_data FROM entity_schemas
            WHERE project_id = ? AND entity_type = ?
            """,
            (project_id, entity_type)
        )

        result = cursor.fetchone()
        if not result:
            return None

        return json.loads(result["schema_data"])

    def get_all_schemas(self, project_id: int) -> List[Dict[str, Any]]:
        """
        获取项目中的所有实体模式

        Args:
            project_id: 项目ID

        Returns:
            模式数据字典列表
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT schema_data FROM entity_schemas
            WHERE project_id = ?
            """,
            (project_id,)
        )

        return [json.loads(row["schema_data"]) for row in cursor.fetchall()]

    def get_all_schema_names(self, project_id: int) -> List[str]:
        """
        获取项目中的所有实体模式名称

        Args:
            project_id: 项目ID

        Returns:
            模式名称列表
        """
        conn = self.db_manager.connect()
        cursor = conn.execute(
            """
            SELECT DISTINCT entity_type FROM entity_schemas
            WHERE project_id = ?
            """,
            (project_id,)
        )

        return [row["entity_type"] for row in cursor.fetchall()]

    def _row_to_entity_declaration(self, row: sqlite3.Row) -> EntityDeclaration:
        """将数据库行转换为实体声明对象"""
        return EntityDeclaration(
            location=Location(
                file_path=Path(row["location_file"]),
                start_line=row["location_line"],
                end_line=row["location_line"],  # 使用相同的行号作为结束行
                start_column=row["location_column"]
            ),
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            name=row["name"],
            raw_data=json.loads(row["raw_data"]),
            source_code=row["source_code"]
        )

    def _row_to_entity_reference(self, row: sqlite3.Row) -> EntityReference:
        """将数据库行转换为实体引用对象"""
        return EntityReference(
            source_entity_id=row["source_entity_id"],
            target_entity_id=row["target_entity_id"],
            context_text=row["reference_text"],
            location=Location(
                file_path=Path(row["location_file"]),
                start_line=row["location_line"],
                end_line=row["location_line"],  # 使用相同的行号作为结束行
                start_column=row["location_column"]
            )
        )