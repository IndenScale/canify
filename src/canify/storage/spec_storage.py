"""
Spec 存储管理器

负责将 spec 规则存储到数据库并从数据库读取。
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import sqlite3

from ..models.spec import SpecificationRule
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class SpecStorageManager:
    """Spec 存储管理器"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化存储管理器

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager

    def store_specs(self, project_id: int, file_path: str, specs: List[SpecificationRule]) -> None:
        """
        存储 spec 规则到数据库

        Args:
            project_id: 项目 ID
            file_path: 文件路径
            specs: spec 规则列表
        """
        conn = self.db_manager.connect()

        try:
            # 获取或创建文件记录
            cursor = conn.execute("SELECT id FROM files WHERE project_id = ? AND file_path = ?", (project_id, file_path))
            file_record = cursor.fetchone()

            if file_record:
                file_id = file_record["id"]
            else:
                from datetime import datetime
                cursor = conn.execute(
                    """
                    INSERT INTO files (project_id, file_path, file_hash, last_modified, status)
                    VALUES (?, ?, ?, ?, 'parsing')
                    """,
                    (project_id, file_path, "", datetime.now().isoformat())
                )
                file_id = cursor.lastrowid

            for spec in specs:
                self._store_single_spec(conn, project_id, file_id, spec)

            conn.commit()
            logger.info(f"成功存储 {len(specs)} 个 spec 规则到文件 {file_path}")

        except Exception as e:
            conn.rollback()
            logger.error(f"存储 spec 规则失败: {e}")
            raise

    def _store_single_spec(
        self,
        conn: sqlite3.Connection,
        project_id: int,
        file_id: int,
        spec: SpecificationRule
    ) -> None:
        """
        存储单个 spec 规则

        Args:
            conn: 数据库连接
            project_id: 项目 ID
            file_id: 文件 ID
            spec: spec 规则
        """
        # 准备数据
        levels_json = json.dumps(spec.levels)
        tags_json = json.dumps(spec.tags) if spec.tags else None

        # 构建 source_code
        source_lines = [
            f"id: {spec.id}",
            f"name: {spec.name}",
            f"description: {spec.description}",
            f"env: {spec.env}",
            f"fixture: {spec.fixture}",
            f"test_case: {spec.test_case}",
            f"levels: {levels_json}",
            f"tags: {tags_json if tags_json else '[]'}"
        ]
        source_code = '\n'.join(source_lines)

        # 插入或更新 spec 规则
        conn.execute("""
            INSERT OR REPLACE INTO spec_rules
            (project_id, file_id, rule_id, name, description, env, fixture, test_case, levels, tags, source_code, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            file_id,
            spec.id,
            spec.name,
            spec.description,
            spec.env,
            spec.fixture,
            spec.test_case,
            levels_json,
            tags_json,
            source_code,
            str(Path.cwd())  # 当前工作目录作为文件路径
        ))

    def get_specs_by_project(self, project_id: int) -> List[SpecificationRule]:
        """
        根据项目 ID 获取所有 spec 规则

        Args:
            project_id: 项目 ID

        Returns:
            SpecificationRule 对象列表
        """
        conn = self.db_manager.connect()

        cursor = conn.execute("""
            SELECT rule_id, name, description, env, fixture, test_case, levels, tags, source_code
            FROM spec_rules
            WHERE project_id = ?
        """, (project_id,))

        specs = []
        for row in cursor:
            spec = self._row_to_specification_rule(row)
            if spec:
                specs.append(spec)

        logger.debug(f"从数据库获取了 {len(specs)} 个 spec 规则")
        return specs

    def get_spec_by_id(self, project_id: int, rule_id: str) -> Optional[SpecificationRule]:
        """
        根据项目 ID 和规则 ID 获取 spec 规则

        Args:
            project_id: 项目 ID
            rule_id: 规则 ID

        Returns:
            SpecificationRule 对象，如果未找到则返回 None
        """
        conn = self.db_manager.connect()

        cursor = conn.execute("""
            SELECT rule_id, name, description, env, fixture, test_case, levels, tags, source_code
            FROM spec_rules
            WHERE project_id = ? AND rule_id = ?
        """, (project_id, rule_id))

        row = cursor.fetchone()
        if row:
            return self._row_to_specification_rule(row)
        return None

    def get_specs_by_tags(self, project_id: int, tags: List[str]) -> List[SpecificationRule]:
        """
        根据标签获取 spec 规则

        Args:
            project_id: 项目 ID
            tags: 标签列表

        Returns:
            SpecificationRule 对象列表
        """
        conn = self.db_manager.connect()

        # 构建标签查询条件
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(f"tags LIKE '%\"{tag}\"%'")

        if not tag_conditions:
            return []

        tag_where = " OR ".join(tag_conditions)

        cursor = conn.execute(f"""
            SELECT rule_id, name, description, env, fixture, test_case, levels, tags, source_code
            FROM spec_rules
            WHERE project_id = ? AND ({tag_where})
        """, (project_id,))

        specs = []
        for row in cursor:
            spec = self._row_to_specification_rule(row)
            if spec:
                specs.append(spec)

        return specs

    def get_specs_by_env(self, project_id: int, env: str) -> List[SpecificationRule]:
        """
        根据执行环境获取 spec 规则

        Args:
            project_id: 项目 ID
            env: 执行环境 (local 或 remote)

        Returns:
            SpecificationRule 对象列表
        """
        conn = self.db_manager.connect()

        cursor = conn.execute("""
            SELECT rule_id, name, description, env, fixture, test_case, levels, tags, source_code
            FROM spec_rules
            WHERE project_id = ? AND env = ?
        """, (project_id, env))

        specs = []
        for row in cursor:
            spec = self._row_to_specification_rule(row)
            if spec:
                specs.append(spec)

        return specs

    def delete_specs_by_file(self, project_id: int, file_path: str) -> None:
        """
        删除指定文件的所有 spec 规则

        Args:
            project_id: 项目 ID
            file_path: 文件路径
        """
        conn = self.db_manager.connect()

        cursor = conn.execute("SELECT id FROM files WHERE project_id = ? AND file_path = ?", (project_id, file_path))
        file_record = cursor.fetchone()

        if not file_record:
            return

        file_id = file_record["id"]

        conn.execute("""
            DELETE FROM spec_rules
            WHERE project_id = ? AND file_id = ?
        """, (project_id, file_id))

        conn.commit()
        logger.info(f"删除了文件 {file_path} 的所有 spec 规则")

    def _row_to_specification_rule(self, row: sqlite3.Row) -> Optional[SpecificationRule]:
        """
        将数据库行转换为 SpecificationRule 对象

        Args:
            row: 数据库行

        Returns:
            SpecificationRule 对象
        """
        try:
            # 解析 JSON 字段
            levels = json.loads(row['levels']) if row['levels'] else {}
            tags = json.loads(row['tags']) if row['tags'] else None

            return SpecificationRule(
                id=row['rule_id'],
                name=row['name'],
                description=row['description'] or '',
                levels=levels,
                fixture=row['fixture'] or '',
                test_case=row['test_case'] or '',
                env=row['env'] or 'local',
                tags=tags
            )

        except Exception as e:
            logger.error(f"转换数据库行到 SpecificationRule 失败: {e}")
            return None

    def get_all_tags(self, project_id: int) -> List[str]:
        """
        获取项目中所有唯一的标签

        Args:
            project_id: 项目 ID

        Returns:
            标签列表
        """
        conn = self.db_manager.connect()

        cursor = conn.execute("""
            SELECT DISTINCT tags FROM spec_rules WHERE project_id = ? AND tags IS NOT NULL
        """, (project_id,))

        tags = set()
        for row in cursor:
            if row['tags']:
                try:
                    tag_list = json.loads(row['tags'])
                    tags.update(tag_list)
                except json.JSONDecodeError:
                    continue

        return sorted(list(tags))