"""
Spec 文件发现器

负责发现和扫描项目中的 spec_*.yaml 文件。
"""

import logging
from pathlib import Path
from typing import List, Iterator
from glob import glob

logger = logging.getLogger(__name__)


class SpecDiscoverer:
    """Spec 文件发现器"""

    def __init__(self, project_root: Path):
        """
        初始化发现器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)

    def discover_spec_files(self) -> List[Path]:
        """
        发现项目中的所有 spec_*.yaml 文件

        Returns:
            spec 文件路径列表
        """
        spec_files = []

        # 使用 glob 模式匹配所有 spec_*.yaml 文件
        pattern = str(self.project_root / "**" / "spec_*.yaml")

        for file_path in glob(pattern, recursive=True):
            spec_files.append(Path(file_path))

        logger.info(f"发现 {len(spec_files)} 个 spec 文件")
        return spec_files

    def discover_spec_files_iter(self) -> Iterator[Path]:
        """
        迭代发现项目中的所有 spec_*.yaml 文件

        Yields:
            spec 文件路径
        """
        pattern = str(self.project_root / "**" / "spec_*.yaml")

        for file_path in glob(pattern, recursive=True):
            yield Path(file_path)

    def get_spec_file_count(self) -> int:
        """
        获取 spec 文件数量

        Returns:
            spec 文件数量
        """
        pattern = str(self.project_root / "**" / "spec_*.yaml")
        return len(glob(pattern, recursive=True))