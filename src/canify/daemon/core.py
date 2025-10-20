"""
Canify Daemon 核心

负责协调文件监听、符号表管理和验证执行。
"""

import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any
from queue import Queue, Empty

from ..storage import DatabaseManager, SymbolTableManager, SpecStorageManager
from ..parsers import EntityDeclarationParser, EntityReferenceParser, EntityFieldReferenceParser
from ..parsers.symbol_extractor import SymbolExtractor
from ..parsers.entity_schema_parser import EntitySchemaParser
from ..extraction.spec_extractor import SpecExtractor
from ..filtering.tag_filter import TagFilter
from ..execution.spec_executor import SpecExecutor
from ..validation.validation_engine import ValidationEngine
from ..ipc.server import IPCServer
from .file_watcher import FileWatcher

logger = logging.getLogger(__name__)


class CanifyDaemon:
    """Canify Daemon 核心类"""

    def __init__(self, project_root: Path, db_path: Optional[Path] = None):
        """
        初始化 Canify Daemon

        Args:
            project_root: 项目根目录
            db_path: 数据库文件路径
        """
        self.project_root = project_root
        self.db_manager = DatabaseManager(db_path)
        self.symbol_table = SymbolTableManager(self.db_manager)
        self.spec_storage = SpecStorageManager(self.db_manager)
        self.file_watcher = FileWatcher(project_root)

        # 解析器
        self.declaration_parser = EntityDeclarationParser()
        self.reference_parser = EntityReferenceParser()
        self.field_reference_parser = EntityFieldReferenceParser()
        self.schema_parser = EntitySchemaParser()
        self.symbol_extractor = SymbolExtractor()
        self.spec_extractor = SpecExtractor(self.project_root)

        # 验证与执行
        self.validation_engine = ValidationEngine(self.symbol_table)
        self.tag_filter = TagFilter()
        self.spec_executor = SpecExecutor(self.project_root)

        # IPC服务器
        self.ipc_server = IPCServer()

        # 事件队列
        self.event_queue: Queue = Queue()
        self.processing_queue: Queue = Queue()

        # 状态管理
        self.is_running = False
        self.project_id: Optional[int] = None

        # 线程
        self.event_thread: Optional[threading.Thread] = None
        self.processing_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动 daemon"""
        if self.is_running:
            logger.warning("Daemon 已经在运行")
            return

        # 初始化数据库
        self.db_manager.initialize_schema()

        # 获取或创建项目记录
        self.project_id = self.symbol_table.get_or_create_project(self.project_root)

        # 清理项目旧数据
        self.symbol_table.clear_project_data(self.project_id)

        # 注册RPC方法
        self._register_rpc_methods()

        # 启动IPC服务器
        port = self.ipc_server.start()

        # 启动文件监听
        self.file_watcher.start(self._handle_file_event)

        # 执行初始全量扫描
        self._perform_initial_scan()

        # 启动事件处理线程
        self.is_running = True
        self.event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)

        self.event_thread.start()
        self.processing_thread.start()

        logger.info(f"Canify Daemon 已启动，项目: {self.project_root}, IPC端口: {port}")

    def _perform_initial_scan(self):
        """
        对项目目录执行一次初始的全量扫描和处理。
        """
        logger.info("开始对项目进行初始扫描...")
        relevant_extensions = ['.md', '.py', '.yaml', '.yml']

        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and file_path.suffix in relevant_extensions:
                relative_path = file_path.relative_to(self.project_root)
                logger.debug(f"初始扫描发现文件: {relative_path}")
                self._handle_file_update(str(relative_path))
        
        logger.info("初始扫描完成。")

    def stop(self) -> None:
        """停止 daemon"""
        if not self.is_running:
            return

        self.is_running = False

        # 停止IPC服务器
        self.ipc_server.stop()

        # 停止文件监听
        self.file_watcher.stop()

        # 等待线程结束
        if self.event_thread:
            self.event_thread.join(timeout=5)
        if self.processing_thread:
            self.processing_thread.join(timeout=5)

        # 关闭数据库连接
        self.db_manager.close()

        logger.info("Canify Daemon 已停止")

    def _register_rpc_methods(self):
        """注册RPC方法"""
        from ..ipc.protocol import RPCMethods

        # Daemon管理方法
        self.ipc_server.register_method(
            RPCMethods.PING,
            self._handle_ping
        )
        self.ipc_server.register_method(
            RPCMethods.GET_STATUS,
            self._handle_get_status
        )

        # 项目相关方法
        self.ipc_server.register_method(
            RPCMethods.GET_PROJECT_STATUS,
            self._handle_get_project_status
        )
        self.ipc_server.register_method(
            RPCMethods.RELOAD_PROJECT,
            self._handle_reload_project
        )

        # 验证相关方法
        self.ipc_server.register_method(
            RPCMethods.VALIDATE,
            self._handle_validate
        )
        self.ipc_server.register_method(
            RPCMethods.LINT,
            self._handle_lint
        )
        self.ipc_server.register_method(
            RPCMethods.VERIFY,
            self._handle_verify
        )

    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理ping请求"""
        return {"message": "pong"}

    def _handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取Daemon状态请求"""
        return {
            "status": "running",
            "project_root": str(self.project_root),
            "is_running": self.is_running,
            "project_id": self.project_id
        }

    def _handle_get_project_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取项目状态请求"""
        return self.get_project_status()

    def _handle_reload_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理重新加载项目请求"""
        # 在实际实现中，这里应该重新扫描整个项目
        return {"message": "项目重新加载已触发"}

    def _handle_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理验证请求"""
        command = params.get("command", "validate")
        target_path = params.get("target_path")
        working_directory = params.get("working_directory")
        options = params.get("options", {})
        tags = options.get("tags")
        remote = options.get("remote", False)
        verbose = options.get("verbose", False)

        try:
            # 1. 从符号表构建视图
            view = self._build_view_from_symbol_table(target_path)

            # 2. 执行基础验证 (schema, references)
            validation_result = self.validation_engine.validate_view(view, self.project_id, verbose=verbose)

            # 3. 执行 Spec 规则验证
            specs_to_run = view.specs

            # 3.1. 按标签过滤
            if tags:
                logger.info(f"应用标签过滤: {tags}")
                specs_to_run = self.tag_filter.filter_specs(specs_to_run, tags)

            # 3.2. 按环境过滤
            env_to_run = "remote" if remote else "local"
            final_specs = [spec for spec in specs_to_run if spec.env == env_to_run or (remote and spec.env == "local")]
            logger.info(f"根据环境 '{env_to_run}' 过滤后，准备执行 {len(final_specs)} 个 spec 规则")

            # 3.3. 执行规则
            if final_specs:
                spec_result = self.spec_executor.execute_specs(final_specs)
                validation_result.merge(spec_result)

            # 4. 转换验证结果为可序列化的字典
            result_dict = self._convert_validation_result_to_dict(validation_result)
            result_dict.update({
                "command": command,
                "target_path": target_path,
                "working_directory": working_directory
            })

            logger.info(f"验证完成: 成功={validation_result.success}, "
                       f"错误={len(validation_result.errors)}, 警告={len(validation_result.warnings)}")

            return result_dict

        except Exception as e:
            logger.error(f"验证处理失败: {e}", exc_info=True)
            return {
                "success": False,
                "errors": [{
                    "message": f"验证处理失败: {e}",
                    "location": "daemon",
                    "rule_id": "daemon-error"
                }],
                "warnings": [],
                "command": command,
                "target_path": target_path,
                "working_directory": working_directory
            }

    def _handle_lint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理lint请求"""
        target_path = params.get("target_path", ".")
        working_directory = params.get("working_directory", str(self.project_root))
        options = params.get("options", {})

        try:
            # 构建目标路径
            if target_path == ".":
                lint_path = self.project_root
            else:
                lint_path = Path(working_directory) / target_path

            # 执行符号提取
            if lint_path.is_file():
                # 单个文件
                result = self.symbol_extractor.extract_from_file(lint_path)
                extracted_symbols = {
                    "files": [result],
                    "summary": result.get("statistics", {})
                }
            else:
                # 目录
                extracted_symbols = self.symbol_extractor.extract_from_directory(lint_path)

            return {
                "success": True,
                "command": "lint",
                "target_path": target_path,
                "working_directory": working_directory,
                "extracted_symbols": extracted_symbols,
                "errors": [],
                "warnings": []
            }

        except Exception as e:
            logger.error(f"lint处理失败: {e}")
            return {
                "success": False,
                "command": "lint",
                "target_path": target_path,
                "working_directory": working_directory,
                "errors": [{
                    "message": f"lint处理失败: {e}",
                    "location": "daemon"
                }],
                "warnings": []
            }

    def _handle_verify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理verify请求"""
        return self._handle_validate(params)

    def _handle_file_event(self, file_path: str, event_type: str) -> None:
        """
        处理文件事件

        Args:
            file_path: 文件路径（相对于项目根目录）
            event_type: 事件类型（created, modified, deleted）
        """
        self.event_queue.put({
            'file_path': file_path,
            'event_type': event_type,
            'timestamp': time.time()
        })

    def _event_loop(self) -> None:
        """事件循环线程"""
        logger.debug("事件循环线程启动")

        while self.is_running:
            try:
                # 从事件队列获取事件，超时1秒
                event = self.event_queue.get(timeout=1)
                self._process_event(event)
                self.event_queue.task_done()

            except Empty:
                # 队列为空，继续循环
                continue
            except Exception as e:
                logger.error(f"事件处理错误: {e}")

        logger.debug("事件循环线程结束")

    def _processing_loop(self) -> None:
        """处理循环线程"""
        logger.debug("处理循环线程启动")

        while self.is_running:
            try:
                # 从处理队列获取任务，超时1秒
                task = self.processing_queue.get(timeout=1)
                self._execute_task(task)
                self.processing_queue.task_done()

            except Empty:
                # 队列为空，继续循环
                continue
            except Exception as e:
                logger.error(f"任务执行错误: {e}")

        logger.debug("处理循环线程结束")

    def _process_event(self, event: Dict[str, Any]) -> None:
        """
        处理单个文件事件

        Args:
            event: 文件事件
        """
        file_path = event['file_path']
        event_type = event['event_type']

        logger.info(f"处理文件事件: {file_path} ({event_type})")

        # 根据事件类型处理
        if event_type in ['created', 'modified']:
            self._handle_file_update(file_path)
        elif event_type == 'deleted':
            self._handle_file_deletion(file_path)

    def _handle_file_update(self, file_path: str) -> None:
        """
        处理文件更新（创建或修改）

        Args:
            file_path: 文件路径
        """
        try:
            # 读取文件内容
            full_path = self.project_root / file_path
            if not full_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 1. 解析文件，获取声明和引用
            declarations = self.declaration_parser.parse(content, full_path)
            references = self.reference_parser.parse(content, full_path)
            field_references = []
            for declaration in declarations:
                field_refs = self.field_reference_parser.parse_from_declaration(declaration, full_path)
                field_references.extend(field_refs)
            all_references = references + field_references

            # 2. 在插入前检查重复声明
            seen_in_this_file = set()
            duplicate_errors = []

            for declaration in declarations:
                # 检查文件内部的重复
                if declaration.entity_id in seen_in_this_file:
                    error_message = f"实体ID '{declaration.entity_id}' 在文件 {file_path} 内部重复声明。"
                    logger.error(error_message)
                    duplicate_errors.append(error_message)
                else:
                    seen_in_this_file.add(declaration.entity_id)

                # 检查与数据库中其他文件的重复
                existing_symbol = self.symbol_table.get_entity_by_id(self.project_id, declaration.entity_id)
                if existing_symbol:
                    error_message = f"实体ID '{declaration.entity_id}' 重复声明。原声明位于: {existing_symbol.location.file_path}"
                    logger.error(error_message)
                    duplicate_errors.append(error_message)

            # 3. 清理并插入新符号（如果没有重复错误）
            if not duplicate_errors:
                self.symbol_table.delete_symbols_by_file(self.project_id, file_path)
                self.spec_storage.delete_specs_by_file(self.project_id, file_path)
                self.symbol_table.insert_symbols(self.project_id, file_path, declarations, all_references)
                logger.info(f"Markdown文件更新完成: {file_path} ({len(declarations)} 声明, {len(all_references)} 引用)")
            else:
                # 有重复错误，只清理符号但不插入新符号
                self.symbol_table.delete_symbols_by_file(self.project_id, file_path)
                combined_error = "\n".join(duplicate_errors)
                self.symbol_table.update_file_status(self.project_id, file_path, 'error', combined_error)
                logger.warning(f"Markdown文件有重复声明，跳过符号插入: {file_path}")

            # 根据文件类型处理其他符号
            if full_path.suffix == '.py':
                schemas = self.schema_parser.parse(content, full_path)
                for schema in schemas:
                    self.symbol_table.insert_schema(self.project_id, file_path, schema)
                logger.info(f"Python文件更新完成: {file_path} ({len(schemas)} schemas)")

            elif full_path.name.startswith('spec_') and full_path.suffix in ['.yaml', '.yml']:
                specs = self.spec_extractor.extract_specs_from_file(full_path)
                if specs:
                    self.spec_storage.store_specs(self.project_id, file_path, specs)
                logger.info(f"Spec文件更新完成: {file_path} ({len(specs)} 规则)")

            # 触发验证（可选）
            self._trigger_validation(file_path)

        except Exception as e:
            logger.error(f"处理文件更新失败 {file_path}: {e}")
            self.symbol_table.update_file_status(self.project_id, file_path, 'error', str(e))

    def _handle_file_deletion(self, file_path: str) -> None:
        """
        处理文件删除

        Args:
            file_path: 文件路径
        """
        try:
            # 从符号表中删除相关符号
            self.symbol_table.delete_symbols_by_file(self.project_id, file_path)
            self.spec_storage.delete_specs_by_file(self.project_id, file_path)
            logger.info(f"文件删除处理完成: {file_path}")

        except Exception as e:
            logger.error(f"处理文件删除失败 {file_path}: {e}")

    def _trigger_validation(self, file_path: str) -> None:
        """
        触发验证

        Args:
            file_path: 文件路径
        """
        # 这里可以添加实时验证逻辑
        # 目前只是记录日志
        logger.debug(f"触发验证: {file_path}")

    def _execute_task(self, task: Dict[str, Any]) -> None:
        """
        执行处理任务

        Args:
            task: 任务数据
        """
        # 这里可以执行更复杂的处理任务
        # 目前只是记录日志
        logger.debug(f"执行任务: {task}")

    def _build_view_from_symbol_table(self, target_path: Optional[str] = None) -> View:
        """
        从符号表构建视图对象

        Args:
            target_path: 目标路径，None 表示整个项目

        Returns:
            视图对象
        """
        from ..models import View, EntityDeclaration, EntityReference

        try:
            # 获取所有实体
            all_entities = self.symbol_table.get_all_entities(self.project_id)

            # 将实体列表转换为字典，key为entity_id
            entities_dict = {entity.entity_id: entity for entity in all_entities}

            # 如果指定了目标路径，过滤实体
            if target_path:
                target_entities = {}
                # 将目标路径转换为绝对路径
                absolute_target_path = str(self.project_root / target_path)
                for entity_id, entity in entities_dict.items():
                    if str(entity.location.file_path).startswith(absolute_target_path):
                        target_entities[entity_id] = entity
                entities = target_entities
            else:
                entities = entities_dict

            # 获取所有引用
            all_references = self.symbol_table.get_all_references(self.project_id)

            # 如果指定了目标路径，过滤引用
            if target_path:
                absolute_target_path = str(self.project_root / target_path)
                references = [
                    ref for ref in all_references
                    if str(ref.location.file_path).startswith(absolute_target_path)
                ]
            else:
                references = all_references

            # 获取所有模式名称
            schema_names = self.symbol_table.get_all_schema_names(self.project_id)

            # 获取所有 spec 规则
            specs = self.spec_storage.get_specs_by_project(self.project_id)

            # 构建视图
            view = View(
                branch="main",  # 简化实现，使用固定分支
                checkpoint_id=f"daemon-{int(time.time())}",
                entities=entities,
                references=references,
                specs=specs,
                schema_names=schema_names
            )

            logger.debug(f"构建视图: {len(entities)} 个实体, {len(references)} 个引用, {len(specs)} 个 specs, {len(schema_names)} 个模式")
            logger.debug(f"实体IDs: {list(entities.keys())}")
            logger.debug(f"引用目标: {[ref.target_entity_id for ref in references]}")

            return view

        except Exception as e:
            logger.error(f"构建视图失败: {e}")
            # 返回空视图
            return View(
                branch="main",
                checkpoint_id="error",
                entities={},
                references=[],
                specs=[],
                schema_names=[]
            )

    def _convert_validation_result_to_dict(self, validation_result) -> Dict[str, Any]:
        """
        将验证结果转换为可序列化的字典

        Args:
            validation_result: 验证结果对象

        Returns:
            可序列化的字典
        """
        from ..models import ValidationError

        errors = []
        for error in validation_result.errors:
            error_dict = {
                "message": error.message,
                "location": str(error.location) if error.location else "unknown",
                "rule_id": error.rule_id,
                "severity": "error" # Default
            }
            if isinstance(error, ValidationError):
                error_dict["severity"] = error.severity.value if hasattr(error.severity, 'value') else str(error.severity)
            errors.append(error_dict)

        warnings = []
        for warning in validation_result.warnings:
            warning_dict = {
                "message": warning.message,
                "location": str(warning.location) if warning.location else "unknown",
                "rule_id": warning.rule_id,
                "severity": "warning" # Default
            }
            if isinstance(warning, ValidationError):
                warning_dict["severity"] = warning.severity.value if hasattr(warning.severity, 'value') else str(warning.severity)
            warnings.append(warning_dict)

        result_dict = {
            "success": validation_result.success,
            "total_checks": validation_result.total_checks,
            "errors": errors,
            "warnings": warnings
        }

        if validation_result.verbose_data:
            result_dict["verbose_data"] = validation_result.verbose_data

        return result_dict

    def get_project_status(self) -> Dict[str, Any]:
        """
        获取项目状态

        Returns:
            项目状态信息
        """
        if not self.project_id:
            return {'status': 'not_initialized'}

        try:
            # 获取实体统计
            all_entities = self.symbol_table.get_all_entities(self.project_id)
            dangling_refs = self.symbol_table.get_dangling_references(self.project_id)

            return {
                'status': 'running',
                'project_root': str(self.project_root),
                'entity_count': len(all_entities),
                'dangling_references': len(dangling_refs),
                'entity_types': {}
            }

        except Exception as e:
            logger.error(f"获取项目状态失败: {e}")
            return {'status': 'error', 'error': str(e)}

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()