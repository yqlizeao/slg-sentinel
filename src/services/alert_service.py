"""
SLG Sentinel — 告警推送服务

当出现异常舆情事件时，通过企业微信/飞书 Webhook 主动通知。
支持配置多个 Webhook 端点。
"""
from __future__ import annotations
import json, logging, os
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# 支持通过环境变量或 secrets.yaml 配置
WECOM_WEBHOOK = os.environ.get("WECOM_WEBHOOK_URL", "")
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK_URL", "")


def send_wecom_alert(title: str, content: str, webhook_url: str = "") -> bool:
    """发送企业微信 Webhook 通知"""
    url = webhook_url or WECOM_WEBHOOK
    if not url:
        logger.debug("未配置企业微信 Webhook，跳过推送")
        return False
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": f"### {title}\n{content}\n> {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"企业微信告警已推送: {title}")
        return True
    except Exception as e:
        logger.warning(f"企业微信推送失败: {e}")
        return False


def send_feishu_alert(title: str, content: str, webhook_url: str = "") -> bool:
    """发送飞书 Webhook 通知"""
    url = webhook_url or FEISHU_WEBHOOK
    if not url:
        logger.debug("未配置飞书 Webhook，跳过推送")
        return False
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": f"🔔 {title}"}},
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content}},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": datetime.now().strftime("%Y-%m-%d %H:%M")}
                ]},
            ],
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"飞书告警已推送: {title}")
        return True
    except Exception as e:
        logger.warning(f"飞书推送失败: {e}")
        return False


def send_alert(title: str, content: str) -> dict[str, bool]:
    """向所有已配置的渠道推送告警"""
    results = {}
    if WECOM_WEBHOOK:
        results["wecom"] = send_wecom_alert(title, content)
    if FEISHU_WEBHOOK:
        results["feishu"] = send_feishu_alert(title, content)
    if not results:
        logger.info("未配置任何 Webhook，告警仅写入日志")
    return results


def check_and_alert_negative_spike(platform: str, current_neg: int, previous_neg: int, threshold: float = 0.5) -> bool:
    """检测负面评论激增并自动告警。threshold=0.5 表示增长超 50% 触发。"""
    if previous_neg <= 0 or current_neg <= previous_neg:
        return False
    growth = (current_neg - previous_neg) / previous_neg
    if growth >= threshold:
        title = f"⚠️ {platform} 负面评论激增"
        content = (
            f"**平台**: {platform}\n"
            f"**当前负面评论**: {current_neg} 条\n"
            f"**上期负面评论**: {previous_neg} 条\n"
            f"**增长幅度**: {growth:.0%}\n"
            f"建议立即查看最新评论内容。"
        )
        send_alert(title, content)
        return True
    return False
