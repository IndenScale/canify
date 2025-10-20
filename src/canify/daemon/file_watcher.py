"""
文件监听器

负责监控文件系统变更，触发符号表更新。
"""

import logging
import time
from pathlib import Path
from typing import Callable, Set, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class CanifyFileEventHandler(FileSystemEventHandler):
    """Canify 文件事件处理器"""

    def __init__(self, callback: Callable[[str, str], None], project_root: Path):
        """
        初始化文件事件处理器

        Args:
            callback: 文件变更回调函数，接收(file_path, event_type)
            project_root: 项目根目录
        """
        self.callback = callback
        self.project_root = project_root
        self.ignored_patterns = {
            '*.pyc', '*.pyo', '*.pyd', '__pycache__',
            '*.swp', '*.swo', '*.tmp', '.git', '.svn',
            'node_modules', '.idea', '.vscode'
        }

    def _should_ignore(self, file_path: str) -> bool:
        """检查文件是否应该被忽略"""
        path = Path(file_path)

        # 检查文件扩展名
        if any(path.match(pattern) for pattern in self.ignored_patterns):
            return True

        # 检查目录名
        for part in path.parts:
            if any(part == pattern.strip('*') for pattern in self.ignored_patterns if not pattern.startswith('*.')):
                return True

        return False

    def _get_relative_path(self, file_path: str) -> str:
        """获取相对于项目根目录的路径"""
        try:
            return str(Path(file_path).relative_to(self.project_root))
        except ValueError:
            # 文件不在项目目录内
            return file_path

    def on_created(self, event: FileSystemEvent) -> None:
        """文件创建事件"""
        if not event.is_directory and not self._should_ignore(event.src_path):
            relative_path = self._get_relative_path(event.src_path)
            logger.debug(f"文件创建: {relative_path}")
            self.callback(relative_path, 'created')

    def on_modified(self, event: FileSystemEvent) -> None:
        """文件修改事件"""
        if not event.is_directory and not self._should_ignore(event.src_path):
            relative_path = self._get_relative_path(event.src_path)
            logger.debug(f"文件修改: {relative_path}")
            self.callback(relative_path, 'modified')

    def on_deleted(self, event: FileSystemEvent) -> None:
        """文件删除事件"""
        if not event.is_directory and not self._should_ignore(event.src_path):
            relative_path = self._get_relative_path(event.src_path)
            logger.debug(f"文件删除: {relative_path}")
            self.callback(relative_path, 'deleted')

    def on_moved(self, event: FileSystemEvent) -> None:
        """文件移动事件"""
        if not event.is_directory:
            src_relative = self._get_relative_path(event.src_path)
            dest_relative = self._get_relative_path(event.dest_path)

            if not self._should_ignore(event.src_path) and not self._should_ignore(event.dest_path):
                logger.debug(f"文件移动: {src_relative} -> {dest_relative}")
                # 处理为删除旧文件 + 创建新文件
                self.callback(src_relative, 'deleted')
                self.callback(dest_relative, 'created')


class FileWatcher:
    """文件监听器"""

    def __init__(self, project_root: Path):
        """
        初始化文件监听器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.observer = Observer()
        self.event_handler: Optional[CanifyFileEventHandler] = None
        self.is_watching = False

    def start(self, callback: Callable[[str, str], None]) -> None:
        """
        开始监听文件变更

        Args:
            callback: 文件变更回调函数
        """
        if self.is_watching:
            logger.warning("文件监听器已经在运行")
            return

        self.event_handler = CanifyFileEventHandler(callback, self.project_root)
        self.observer.schedule(
            self.event_handler,
            str(self.project_root),
            recursive=True
        )

        self.observer.start()
        self.is_watching = True
        logger.info(f"开始监听文件变更: {self.project_root}")

    def stop(self) -> None:
        """停止监听文件变更"""
        if not self.is_watching:
            return

        self.observer.stop()
        self.observer.join()
        self.is_watching = False
        logger.info("停止监听文件变更")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()