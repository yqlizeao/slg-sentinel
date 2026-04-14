"""
SLG Sentinel CSV 存储引擎

CSVStore 是全系统唯一的数据持久层。
- 使用 Python 标准库 csv 模块，不引入 pandas 依赖
- CSV 编码统一 UTF-8 with BOM（兼容 Excel 直接打开中文）
- 幂等性：同一天重复运行不会产生重复数据（通过 video_id 去重）
"""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import fields, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Type, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

# 默认数据根目录
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# UTF-8 BOM 前缀
BOM = "\ufeff"


class CSVStore:
    """CSV 读写引擎"""

    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(
        self,
        platform: str,
        data_type: str,
        date_str: str,
        video_id: str | None = None,
    ) -> Path:
        """
        生成 CSV 文件路径。

        文件路径规则：
        - 视频快照: data/{platform}/videos/{YYYY-MM-DD}_videos.csv
        - 评论: data/{platform}/comments/{YYYY-MM-DD}_{video_id}_comments.csv
        - TapTap评论: data/taptap/reviews/{YYYY-MM-DD}_reviews.csv
        - 每日快照: data/snapshots/{YYYY-MM-DD}_snapshots.csv
        """
        if data_type == "snapshots":
            dir_path = self.data_dir / "snapshots"
            filename = f"{date_str}_snapshots.csv"
        elif data_type == "comments" and video_id:
            dir_path = self.data_dir / platform / "comments"
            filename = f"{date_str}_{video_id}_comments.csv"
        elif data_type == "reviews":
            dir_path = self.data_dir / platform / "reviews"
            filename = f"{date_str}_reviews.csv"
        else:
            dir_path = self.data_dir / platform / data_type
            filename = f"{date_str}_{data_type}.csv"

        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / filename

    def save(
        self,
        dataclass_list: list,
        platform: str,
        data_type: str,
        date_str: str | None = None,
        video_id: str | None = None,
    ) -> Path | None:
        """
        自动按日期保存到 data/{platform}/{data_type}/{YYYY-MM-DD}.csv

        Args:
            dataclass_list: dataclass 实例列表
            platform: 平台名（bilibili/youtube/taptap 等）
            data_type: 数据类型（videos/comments/reviews/snapshots）
            date_str: 日期字符串，默认今天（YYYY-MM-DD）
            video_id: 视频 ID（仅评论文件需要）

        Returns:
            写入的文件路径，如果列表为空则返回 None
        """
        if not dataclass_list:
            logger.warning("数据列表为空，跳过保存")
            return None

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        file_path = self._get_file_path(platform, data_type, date_str, video_id)

        # 获取字段名（从 dataclass 定义）
        field_names = [f.name for f in fields(dataclass_list[0])]

        # 幂等性：读取已有数据，去重
        existing_ids = set()
        id_field = self._get_id_field(data_type)

        if file_path.exists() and id_field:
            try:
                existing_data = self._read_csv_raw(file_path)
                for row in existing_data:
                    if id_field in row:
                        existing_ids.add(row[id_field])
            except Exception as e:
                logger.warning(f"读取已有文件失败，将覆盖写入: {e}")
                existing_ids = set()

        # 过滤已存在的记录
        new_records = []
        for item in dataclass_list:
            item_dict = asdict(item)
            if id_field and item_dict.get(id_field) in existing_ids:
                logger.debug(f"跳过已存在的记录: {item_dict.get(id_field)}")
                continue
            new_records.append(item_dict)

        if not new_records and file_path.exists():
            logger.info(f"无新数据需要写入: {file_path}")
            return file_path

        # 写入模式：追加或新建
        write_mode = "a" if file_path.exists() and existing_ids else "w"

        with open(file_path, write_mode, newline="", encoding="utf-8") as f:
            # 新文件写入 BOM 和表头
            if write_mode == "w":
                f.write(BOM)
                writer = csv.DictWriter(f, fieldnames=field_names)
                writer.writeheader()
            else:
                writer = csv.DictWriter(f, fieldnames=field_names)

            for record in new_records:
                writer.writerow(record)

        logger.info(f"已保存 {len(new_records)} 条记录到 {file_path}")
        return file_path

    def load(
        self,
        dataclass_type: Type[T],
        platform: str,
        data_type: str,
        date_range: tuple[str, str] | None = None,
        date_str: str | None = None,
        video_id: str | None = None,
    ) -> list[T]:
        """
        读取指定日期范围的 CSV，返回 dataclass 列表。

        Args:
            dataclass_type: 目标 dataclass 类型
            platform: 平台名
            data_type: 数据类型
            date_range: 日期范围元组 (start_date, end_date)，格式 YYYY-MM-DD
            date_str: 单个日期（与 date_range 二选一）
            video_id: 视频 ID（仅评论文件）

        Returns:
            dataclass 实例列表
        """
        results = []

        if date_str:
            file_path = self._get_file_path(platform, data_type, date_str, video_id)
            if file_path.exists():
                results.extend(self._load_single_file(dataclass_type, file_path))
        elif date_range:
            start = datetime.strptime(date_range[0], "%Y-%m-%d")
            end = datetime.strptime(date_range[1], "%Y-%m-%d")
            current = start
            while current <= end:
                d = current.strftime("%Y-%m-%d")
                file_path = self._get_file_path(platform, data_type, d, video_id)
                if file_path.exists():
                    results.extend(self._load_single_file(dataclass_type, file_path))
                current += timedelta(days=1)
        else:
            # 加载目录下所有文件
            if data_type == "snapshots":
                dir_path = self.data_dir / "snapshots"
            else:
                dir_path = self.data_dir / platform / data_type
            if dir_path.exists():
                for csv_file in sorted(dir_path.glob("*.csv")):
                    results.extend(self._load_single_file(dataclass_type, csv_file))

        return results

    def get_weekly_delta(
        self,
        platform: str,
        video_id: str,
        reference_date: str | None = None,
    ) -> dict[str, int]:
        """
        计算本周 − 上周的指标增量。

        Args:
            platform: 平台名
            video_id: 视频 ID
            reference_date: 参考日期（默认今天），格式 YYYY-MM-DD

        Returns:
            增量字典，如 {'view_count': 1234, 'like_count': 56, ...}
        """
        from .models import VideoSnapshot

        if reference_date is None:
            reference_date = datetime.now().strftime("%Y-%m-%d")

        ref = datetime.strptime(reference_date, "%Y-%m-%d")
        week_ago = (ref - timedelta(days=7)).strftime("%Y-%m-%d")

        # 获取本周和上周的快照
        current_snapshots = self.load(
            VideoSnapshot, platform, "snapshots", date_str=reference_date
        )
        previous_snapshots = self.load(
            VideoSnapshot, platform, "snapshots", date_str=week_ago
        )

        current = None
        previous = None

        for s in current_snapshots:
            if s.video_id == video_id:
                current = s
                break

        for s in previous_snapshots:
            if s.video_id == video_id:
                previous = s
                break

        # 计算增量的数值字段
        numeric_fields = [
            "view_count",
            "like_count",
            "comment_count",
            "share_count",
            "favorite_count",
            "coin_count",
            "danmaku_count",
        ]

        delta = {}
        for field_name in numeric_fields:
            current_val = getattr(current, field_name, 0) if current else 0
            previous_val = getattr(previous, field_name, 0) if previous else 0
            delta[field_name] = current_val - previous_val

        return delta

    def _load_single_file(self, dataclass_type: Type[T], file_path: Path) -> list[T]:
        """从单个 CSV 文件加载数据"""
        results = []
        try:
            rows = self._read_csv_raw(file_path)
            dc_fields = {f.name: f for f in fields(dataclass_type)}

            for row in rows:
                # 类型转换
                converted = {}
                for key, value in row.items():
                    if key not in dc_fields:
                        continue
                    field_type = dc_fields[key].type
                    try:
                        if field_type == "int" or field_type is int:
                            converted[key] = int(value) if value else 0
                        else:
                            converted[key] = value or ""
                    except (ValueError, TypeError):
                        converted[key] = value or ""

                results.append(dataclass_type(**converted))
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")

        return results

    def _read_csv_raw(self, file_path: Path) -> list[dict]:
        """读取 CSV 文件，自动处理 BOM"""
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return list(reader)

    @staticmethod
    def _get_id_field(data_type: str) -> str | None:
        """根据数据类型返回用于去重的 ID 字段名"""
        id_map = {
            "videos": "video_id",
            "comments": "comment_id",
            "reviews": "review_id",
            "snapshots": "video_id",
            "user_games": "user_id",
        }
        return id_map.get(data_type)
