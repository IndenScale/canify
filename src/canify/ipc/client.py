"""
IPC Socket客户端

负责与Daemon的IPC服务器通信。
"""

import socket
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .protocol import RPCRequest, RPCResponse, IPCMessageEncoder, IPCMessageDecoder

logger = logging.getLogger(__name__)


class IPCClient:
    """IPC Socket客户端"""

    def __init__(self, host: str = "127.0.0.1", port: Optional[int] = None):
        """
        初始化IPC客户端

        Args:
            host: 服务器地址
            port: 服务器端口，如果为None则从文件读取
        """
        self.host = host
        self.port = port
        self.timeout = 10  # 秒

        # 端口文件路径
        self.port_file = Path.home() / ".canify" / "daemon.port"

        # 如果没有指定端口，尝试从文件读取
        if self.port is None:
            self.port = self._read_port_from_file()

    def _read_port_from_file(self) -> Optional[int]:
        """
        从端口文件读取端口号

        Returns:
            端口号，如果文件不存在则返回None
        """
        try:
            if self.port_file.exists():
                with open(self.port_file, 'r') as f:
                    port_str = f.read().strip()
                    return int(port_str)
        except Exception as e:
            logger.error(f"读取端口文件失败: {e}")

        return None

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        调用RPC方法

        Args:
            method: 方法名
            params: 参数

        Returns:
            响应结果

        Raises:
            ConnectionError: 连接失败
            TimeoutError: 超时
        """
        if self.port is None:
            raise ConnectionError("无法确定Daemon端口，请确保Daemon正在运行")

        # 创建请求
        request = RPCRequest(
            id=1,  # 简化实现，使用固定ID
            method=method,
            params=params or {}
        )

        # 发送请求并获取响应
        return self._send_request(request)

    def _send_request(self, request: RPCRequest) -> Dict[str, Any]:
        """
        发送RPC请求

        Args:
            request: RPC请求

        Returns:
            响应数据

        Raises:
            ConnectionError: 连接失败
            TimeoutError: 超时
        """
        try:
            # 创建Socket连接
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))

                # 发送请求
                request_str = json.dumps(request.model_dump(), cls=IPCMessageEncoder)
                sock.sendall(request_str.encode('utf-8'))
                sock.shutdown(socket.SHUT_WR) # 发送完毕

                # 接收完整的响应
                response_parts = []
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response_parts.append(data)
                
                response_data = b"".join(response_parts)
                response_str = response_data.decode('utf-8')

                # 解析响应
                response_dict = json.loads(response_str)
                response = RPCResponse(**response_dict)

                # 检查错误
                if response.error:
                    error_msg = response.error.get("message", "未知错误")
                    raise ConnectionError(f"RPC调用失败: {error_msg}")

                return response.result or {}

        except socket.timeout:
            raise TimeoutError(f"连接Daemon超时 ({self.timeout}秒)")
        except ConnectionRefusedError:
            raise ConnectionError(f"无法连接到Daemon ({self.host}:{self.port})")
        except Exception as e:
            raise ConnectionError(f"RPC调用失败: {e}")

    def ping(self) -> bool:
        """
        测试Daemon连接

        Returns:
            是否连接成功
        """
        try:
            result = self.call("ping")
            return result.get("message") == "pong"
        except Exception as e:
            logger.debug(f"ping失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取Daemon状态

        Returns:
            状态信息

        Raises:
            ConnectionError: 连接失败
        """
        return self.call("get_status")

    def is_daemon_running(self) -> bool:
        """
        检查Daemon是否在运行

        Returns:
            Daemon是否在运行
        """
        return self.ping()