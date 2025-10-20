"""
IPC通信协议定义

定义Daemon与CLI之间的JSON-RPC通信协议。
"""

import json
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class RPCRequest(BaseModel):
    """JSON-RPC请求"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC版本")
    id: Optional[Union[int, str]] = Field(description="请求ID")
    method: str = Field(description="方法名")
    params: Optional[Dict[str, Any]] = Field(default=None, description="参数")


class RPCResponse(BaseModel):
    """JSON-RPC响应"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC版本")
    id: Optional[Union[int, str]] = Field(description="请求ID")
    result: Optional[Any] = Field(default=None, description="结果")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")


class RPCMessage(BaseModel):
    """RPC消息基类"""
    type: MessageType = Field(description="消息类型")
    data: Union[RPCRequest, RPCResponse] = Field(description="消息数据")


class IPCMessageEncoder(json.JSONEncoder):
    """IPC消息JSON编码器"""

    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


class IPCMessageDecoder:
    """IPC消息JSON解码器"""

    @staticmethod
    def decode(message: str) -> RPCMessage:
        """
        解码JSON字符串为RPCMessage

        Args:
            message: JSON字符串

        Returns:
            RPCMessage对象
        """
        data = json.loads(message)

        # 判断消息类型
        if "method" in data:
            # 这是请求消息
            request = RPCRequest(**data)
            return RPCMessage(type=MessageType.REQUEST, data=request)
        else:
            # 这是响应消息
            response = RPCResponse(**data)
            return RPCMessage(type=MessageType.RESPONSE, data=response)


# 预定义的RPC方法
class RPCMethods:
    """RPC方法定义"""

    # Daemon管理
    PING = "ping"
    GET_STATUS = "get_status"
    SHUTDOWN = "shutdown"

    # 项目相关
    GET_PROJECT_STATUS = "get_project_status"
    RELOAD_PROJECT = "reload_project"

    # 验证相关
    VALIDATE = "validate"
    LINT = "lint"
    VERIFY = "verify"


class ErrorCodes:
    """错误码定义"""

    # JSON-RPC标准错误码
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Canify自定义错误码
    DAEMON_NOT_READY = -32000
    PROJECT_NOT_FOUND = -32001
    VALIDATION_ERROR = -32002