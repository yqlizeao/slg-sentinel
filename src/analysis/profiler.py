"""
SLG Sentinel — 用户画像系统

通过读取用户的评论数据（及其所属视频的属性）来推断轻量级用户画像。
在完整体系中，这一步可接入大模型或更深入的用户动态爬虫，此处做基于规则的启发式推演，避免产生过高成本。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from src.core.csv_store import CSVStore
from src.core.models import Comment, UserProfile, VideoSnapshot

logger = logging.getLogger(__name__)

# 面向 PC 单机 SLG 的核心玩家派系特征词
TAG_PC_TARGET = {"全战", "单机", "文明", "光荣", "买断", "三国志14", "三14", "三国志11", "单机版"}
TAG_MOBILE_REFUGEE = {"退坑", "弃坑", "氪", "充", "累", "打卡", "上班", "卖号", "韭菜", "648", "毁三观", "毫无体验", "当头棒喝"}
TAG_HARDCORE = {"大地图", "内政", "机制", "沙盘", "数值碾压", "配将", "开荒", "战术", "纵深"}
TAG_CASUAL = {"种地", "风景", "养老", "抽卡", "随便玩", "立绘", "好看"}


class UserProfiler:
    """基于规则与上下文启发式分析的用户画像生成器"""

    def __init__(self):
        self.store = CSVStore()

    def profile_video_users(
        self, platform: str, video_id: str, max_users: int = 100, date_str: str | None = None
    ) -> List[UserProfile]:
        """
        基于给定视频的评论提取参与用户的画像。
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # 加载视频信息（为了获取上下文游戏类型）
        videos = self.store.load(VideoSnapshot, platform, "videos", date_str=date_str)
        context_tags = ""
        for v in videos:
            if v.video_id == video_id:
                context_tags = v.tags
                break

        # 加载评论
        comments = self.store.load(Comment, platform, "comments", date_str=date_str, video_id=video_id)
        if not comments:
            logger.warning(f"由于缺少评论数据，无法提取 {platform} 视频 {video_id} 的用户画像")
            return []

        profiles = []
        # 按用户聚合评论
        user_comments_map = {}
        for c in comments:
            if not c.author_id:
                continue
            if c.author_id not in user_comments_map:
                user_comments_map[c.author_id] = {
                    "author": c.author,
                    "location": c.ip_location,
                    "texts": [],
                }
            user_comments_map[c.author_id]["texts"].append(c.content)

        count = 0
        for uid, data in user_comments_map.items():
            if count >= max_users:
                break
            
            texts = data["texts"]
            combined_text = " ".join(texts).lower()

            # 1. 启发式年龄段推断
            # 真实生产环境中可通过时间、习惯用语推测，这里用 IP 和文本口吻做简易映射
            age_group = "18-25"  # 默认年轻群体
            if any(w in combined_text for w in ["学生", "上课", "放假", "宿舍", "期末"]):
                age_group = "18-22"
            elif any(w in combined_text for w in ["上班", "下班", "工资", "摸鱼", "公司"]):
                age_group = "25-35"

            # 2. 付费意愿推断
            payer_type = "free"
            if any(w in combined_text for w in ["氪", "充", "万", "首充"]):
                if any(w in combined_text for w in ["满红", "几万", "氪金大佬"]):
                    payer_type = "whale"
                else:
                    payer_type = "dolphin"

            # 3. 标签推断 (面向单机视角的立体成分)
            tags_set = set()
            for w in TAG_PC_TARGET:
                if w in combined_text: tags_set.add("端游遗老")
            for w in TAG_MOBILE_REFUGEE:
                if w in combined_text: tags_set.add("重氪难民")
            for w in TAG_HARDCORE:
                if w in combined_text: tags_set.add("硬核考究党")
            for w in TAG_CASUAL:
                if w in combined_text: tags_set.add("休闲风景党")

            if context_tags and "slg" in context_tags.lower():
                tags_set.add("SLG受众")
            elif not tags_set:
                tags_set.add("散人玩家")

            last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            profile = UserProfile(
                platform=platform,
                user_id=uid,
                username=data["author"],
                age_group=age_group,
                spend_type=payer_type,
                tags=",".join(tags_set),
                location=data["location"],
                last_active_time=last_active,
            )
            profiles.append(profile)
            count += 1

        logger.info(f"生成了 {len(profiles)} 个用户画像 (基于视频 {video_id})")
        return profiles

    def save_profiles(self, profiles: List[UserProfile], platform: str) -> None:
        """保存用户画像到独立存储（统一汇集在 data/profiles/）"""
        if not profiles:
            return
        
        try:
            # 使用 platform = "profiles" 强制 csv_store 路由到 data/profiles/user_games
            # 把源平台名称作为 date_str 传入，生成例如 bilibili_user_games.csv
            self.store.save(profiles, platform="profiles", data_type="user_games", date_str=platform)
            logger.info(f"成功沉淀 {len(profiles)} 海量画像记录至 DB")
        except Exception as e:
            logger.error(f"保存画像失败: {e}")
