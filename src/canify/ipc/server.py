"""
IPC Socket服务器

负责处理来自CLI的RPC请求。
"""

import socket
import threading
import logging
import json
from typing import Dict, Any, Callable, Optional
from pathlib import Path

from .protocol import (
    RPCRequest, RPCResponse, RPCMessage, IPCMessageEncoder,
    IPCMessageDecoder, RPCMethods, ErrorCodes
)

logger = logging.getLogger(__name__)


class IPCServer:
    """IPC Socket服务器"""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        """
        初始化IPC服务器

        Args:
            host: 监听地址
            port: 监听端口，0表示自动分配
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.server_thread: Optional[threading.Thread] = None

        # RPC方法注册表
        self.methods: Dict[str, Callable] = {}

        # 端口文件路径
        self.port_file = Path.home() / ".canify" / "daemon.port"

        # 注册默认方法
        self._register_default_methods()

    def _register_default_methods(self):
        """注册默认RPC方法"""
        self.register_method(RPCMethods.PING, self._handle_ping)
        self.register_method(RPCMethods.GET_STATUS, self._handle_get_status)
        self.register_method(RPCMethods.SHUTDOWN, self._handle_shutdown)

    def register_method(self, method_name: str, handler: Callable):
        """
        注册RPC方法

        Args:
            method_name: 方法名
            handler: 处理方法
        """
        self.methods[method_name] = handler
        logger.debug(f"注册RPC方法: {method_name}")

    def start(self) -> int:
        """
        启动IPC服务器

        Returns:
            实际监听的端口号
        """
        if self.is_running:
            logger.warning("IPC服务器已经在运行")
            return self.port

        # 创建Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 绑定地址
        self.socket.bind((self.host, self.port))
        self.port = self.socket.getsockname()[1]

        # 开始监听
        self.socket.listen(5)
        self.is_running = True

        # 保存端口号到文件
        self._save_port_to_file()

        # 启动服务器线程
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()

        logger.info(f"IPC服务器已启动，监听端口: {self.port}")
        return self.port

    def stop(self):
        """停止IPC服务器"""
        if not self.is_running:
            return

        self.is_running = False

        # 关闭Socket
        if self.socket:
            self.socket.close()
            self.socket = None

        # 删除端口文件
        self._remove_port_file()

        logger.info("IPC服务器已停止")

    def _save_port_to_file(self):
        """保存端口号到文件"""
        try:
            self.port_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.port_file, 'w') as f:
                f.write(str(self.port))
            logger.debug(f"端口号已保存到: {self.port_file}")
        except Exception as e:
            logger.error(f"保存端口文件失败: {e}")

    def _remove_port_file(self):
        """删除端口文件"""
        try:
            if self.port_file.exists():
                self.port_file.unlink()
                logger.debug("端口文件已删除")
        except Exception as e:
            logger.error(f"删除端口文件失败: {e}")

    def _server_loop(self):
        """服务器主循环"""
        logger.debug("服务器主循环启动")

        while self.is_running:
            try:
                # 接受客户端连接
                client_socket, address = self.socket.accept()
                logger.debug(f"客户端连接: {address}")

                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()

            except socket.error as e:
                if self.is_running:
                    logger.error(f"接受客户端连接失败: {e}")
                break

        logger.debug("服务器主循环结束")

    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """
        处理客户端连接

        Args:
            client_socket: 客户端Socket
            address: 客户端地址
        """
        try:
            # 接收数据
            data = client_socket.recv(4096)
            if not data:
                return

            # 解码消息
            message_str = data.decode('utf-8')
            logger.debug(f"收到消息: {message_str}")

            # 处理RPC请求
            response = self._process_rpc_request(message_str)

            # 发送响应
            response_str = json.dumps(response, cls=IPCMessageEncoder)
            client_socket.send(response_str.encode('utf-8'))

        except Exception as e:
            logger.error(f"处理客户端请求失败: {e}")
            # 发送错误响应
            error_response = RPCResponse(
                id=None,
                error={
                    "code": ErrorCodes.INTERNAL_ERROR,
                    "message": f"处理请求时发生错误: {e}"
                }
            )
            error_str = json.dumps(error_response.model_dump())
            client_socket.send(error_str.encode('utf-8'))
        finally:
            client_socket.close()

    def _process_rpc_request(self, message_str: str) -> Dict[str, Any]:
        """
        处理RPC请求

        Args:
            message_str: 请求消息字符串

        Returns:
            响应数据
        """
        try:
            # 解码消息
            message = IPCMessageDecoder.decode(message_str)

            if message.type != "request":
                return RPCResponse(
                    id=None,
                    error={
                        "code": ErrorCodes.INVALID_REQUEST,
                        "message": "仅支持请求消息"
                    }
                ).model_dump()

            request: RPCRequest = message.data

            # 查找处理方法
            if request.method not in self.methods:
                return RPCResponse(
                    id=request.id,
                    error={
                        "code": ErrorCodes.METHOD_NOT_FOUND,
                        "message": f"方法未找到: {request.method}"
                    }
                ).model_dump()

            # 调用处理方法
            handler = self.methods[request.method]
            result = handler(request.params or {})

            return RPCResponse(
                id=request.id,
                result=result
            ).model_dump()

        except json.JSONDecodeError as e:
            return RPCResponse(
                id=None,
                error={
                    "code": ErrorCodes.PARSE_ERROR,
                    "message": f"JSON解析错误: {e}"
                }
            ).model_dump()
        except Exception as e:
            return RPCResponse(
                id=None,
                error={
                    "code": ErrorCodes.INTERNAL_ERROR,
                    "message": f"内部错误: {e}"
                }
            ).model_dump()

    # 默认处理方法
    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理ping请求"""
        return {"message": "pong", "timestamp": "2025-10-20T00:00:00Z"}

    def _handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取状态请求"""
        return {
            "status": "running",
            "version": "0.2.0",
            "uptime": "0s",
            "clients_connected": 0
        }

    def _handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理关闭请求"""
        logger.info("收到关闭请求")

        # 在单独的线程中停止服务器，避免阻塞响应
        def shutdown_async():
            import time
            time.sleep(0.1)  # 确保响应先发送给客户端
            self.stop()

        import threading
        shutdown_thread = threading.Thread(target=shutdown_async, daemon=True)
        shutdown_thread.start()

        return {"message": "shutdown initiated"}

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()