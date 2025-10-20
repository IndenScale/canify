"""
Canify Daemon 客户端

负责与 Canify Daemon 进行通信，发送验证请求并接收结果。
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from ..canify.ipc.client import IPCClient

logger = logging.getLogger(__name__)


class DaemonClient:
    """Canify Daemon 客户端"""

    def __init__(self, host: str = "127.0.0.1", port: Optional[int] = None):
        """
        初始化 daemon 客户端

        Args:
            host: daemon 主机地址
            port: daemon 端口，如果为None则自动检测
        """
        self.ipc_client = IPCClient(host=host, port=port)

    def is_daemon_running(self) -> bool:
        """
        检查 daemon 是否在运行

        Returns:
            daemon 是否运行
        """
        return self.ipc_client.is_daemon_running()

    def send_validation_request(
        self,
        command: str,
        target_path: Optional[str] = None,
        working_directory: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送验证请求到 daemon

        Args:
            command: 命令类型 ("lint", "verify", "validate")
            target_path: 目标路径，None 表示整个项目
            working_directory: CLI 工作目录
            options: 命令行选项

        Returns:
            验证结果

        Raises:
            ConnectionError: 连接 daemon 失败
            TimeoutError: 请求超时
        """
        if working_directory is None:
            working_directory = str(Path.cwd())

        if options is None:
            options = {}

        # 构建请求参数
        params = {
            "command": command,
            "target_path": target_path,
            "working_directory": working_directory,
            "options": options,
            "timestamp": time.time()
        }

        logger.debug(f"发送验证请求: {params}")

        try:
            # 使用IPC客户端发送请求
            result = self.ipc_client.call("validate", params)
            logger.debug(f"收到验证响应: {result}")
            return result

        except Exception as e:
            raise ConnectionError(f"与 daemon 通信失败: {e}")

    def get_daemon_status(self) -> Dict[str, Any]:
        """
        获取 daemon 状态

        Returns:
            daemon 状态信息
        """
        try:
            return self.ipc_client.get_status()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def stop_daemon(self) -> bool:
        """
        停止 daemon

        Returns:
            是否成功停止
        """
        try:
            result = self.ipc_client.call("shutdown")
            return result.get("message") == "shutdown initiated"
        except Exception:
            return False