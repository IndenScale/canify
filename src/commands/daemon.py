"""
Canify Daemon 命令

负责启动、停止和管理 Canify Daemon。
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from ..canify.daemon.core import CanifyDaemon
from ..client.daemon_client import DaemonClient

logger = logging.getLogger(__name__)


def run_daemon_start(project_path: str = ".") -> int:
    """
    启动 Canify Daemon，如果已有实例在运行，则直接退出。

    Args:
        project_path: 项目路径，默认为当前目录

    Returns:
        退出码
    """
    # 检查是否已有 daemon 实例在运行
    client = DaemonClient()
    if client.is_daemon_running():
        print("✅ Canify Daemon 已在运行中。")
        return 0

    try:
        project_root = Path(project_path).absolute()

        if not project_root.exists():
            print(f"错误: 项目路径不存在: {project_path}")
            return 1

        if not project_root.is_dir():
            print(f"错误: 项目路径必须是目录: {project_path}")
            return 1

        print(f"启动 Canify Daemon...")
        print(f"项目路径: {project_root}")

        # 创建并启动 daemon
        daemon = CanifyDaemon(project_root)
        daemon.start()

        print("✅ Canify Daemon 已启动")
        print("\n按 Ctrl+C 停止 daemon")

        try:
            # 保持运行
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止 daemon...")
            daemon.stop()
            print("✅ Canify Daemon 已停止")

        return 0

    except Exception as e:
        logger.error(f"启动 daemon 失败: {e}")
        print(f"❌ 启动 daemon 失败: {e}")
        return 1


def run_daemon_stop() -> int:
    """
    停止 Canify Daemon

    Returns:
        退出码
    """
    print("停止 Canify Daemon...")

    # TODO: 实现通过进程间通信停止运行中的 daemon
    # 目前这个功能需要后续实现

    print("⚠️  停止功能需要后续实现")
    print("目前请使用 Ctrl+C 停止正在运行的 daemon")
    return 0


def run_daemon_status(project_path: str = ".") -> int:
    """
    显示 Canify Daemon 状态

    Args:
        project_path: 项目路径，默认为当前目录

    Returns:
        退出码
    """
    try:
        project_root = Path(project_path).absolute()

        if not project_root.exists():
            print(f"错误: 项目路径不存在: {project_path}")
            return 1

        print(f"Canify Daemon 状态")
        print(f"项目路径: {project_root}")

        # 检查 daemon 是否在运行
        client = DaemonClient()
        if client.is_daemon_running():
            print("\n✅ 状态: 运行中")

            # 获取详细状态信息
            try:
                # 首先尝试获取项目状态（包含实体统计）
                project_status = client.ipc_client.call("get_project_status")
                if project_status.get("status") == "running":
                    print(f"   实体数量: {project_status.get('entity_count', 0)}")
                    print(f"   悬空引用: {project_status.get('dangling_references', 0)}")
                    print(f"   项目根目录: {project_status.get('project_root', '未知')}")
                else:
                    # 如果项目状态获取失败，使用基础状态
                    daemon_status = client.get_daemon_status()
                    print(f"   项目根目录: {daemon_status.get('project_root', '未知')}")
            except Exception as e:
                # 如果获取项目状态失败，使用基础状态
                daemon_status = client.get_daemon_status()
                print(f"   项目根目录: {daemon_status.get('project_root', '未知')}")
                print(f"   状态详情: 基础状态可用，项目统计信息获取失败")
        else:
            print("\n❌ 状态: 未运行")
            print("使用 'canify daemon start' 启动 daemon")

        return 0

    except Exception as e:
        logger.error(f"获取 daemon 状态失败: {e}")
        print(f"❌ 获取 daemon 状态失败: {e}")
        return 1