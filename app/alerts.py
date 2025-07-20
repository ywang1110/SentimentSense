"""
告警系统模块
"""
import asyncio
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Any, Optional, List
from enum import Enum

import requests

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert:
    """告警对象"""
    
    def __init__(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.WARNING,
        source: str = "SentimentSense",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.message = message
        self.level = level
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.id = f"{self.source}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alert_history: List[Alert] = []
        self.alert_cooldown: Dict[str, datetime] = {}
        self.cooldown_period = timedelta(minutes=15)  # 15分钟冷却期
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """检查是否应该发送告警（避免告警风暴）"""
        if alert_key not in self.alert_cooldown:
            return True
        
        last_sent = self.alert_cooldown[alert_key]
        return datetime.utcnow() - last_sent > self.cooldown_period
    
    async def send_alert(self, alert: Alert) -> bool:
        """发送告警"""
        alert_key = f"{alert.source}_{alert.title}"
        
        if not self._should_send_alert(alert_key):
            logger.debug(f"Alert suppressed due to cooldown: {alert.title}")
            return False
        
        # 记录告警历史
        self.alert_history.append(alert)
        if len(self.alert_history) > 1000:  # 保留最近1000条告警
            self.alert_history = self.alert_history[-1000:]
        
        success = False
        
        # 发送邮件告警
        if settings.ALERT_EMAIL:
            try:
                await self._send_email_alert(alert)
                success = True
                logger.info(f"Email alert sent: {alert.title}")
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        # 发送 Slack 告警
        if settings.ALERT_SLACK_WEBHOOK:
            try:
                await self._send_slack_alert(alert)
                success = True
                logger.info(f"Slack alert sent: {alert.title}")
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
        
        if success:
            self.alert_cooldown[alert_key] = datetime.utcnow()
        
        return success
    
    async def _send_email_alert(self, alert: Alert):
        """发送邮件告警"""
        # 这里简化实现，实际生产环境需要配置 SMTP 服务器
        logger.info(f"Would send email alert: {alert.title} - {alert.message}")
    
    async def _send_slack_alert(self, alert: Alert):
        """发送 Slack 告警"""
        if not settings.ALERT_SLACK_WEBHOOK:
            return
        
        # 根据告警级别选择颜色
        color_map = {
            AlertLevel.INFO: "#36a64f",      # 绿色
            AlertLevel.WARNING: "#ff9500",   # 橙色
            AlertLevel.ERROR: "#ff0000",     # 红色
            AlertLevel.CRITICAL: "#8b0000"   # 深红色
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.level, "#ff9500"),
                    "title": f"🚨 {alert.title}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Service",
                            "value": alert.source,
                            "short": True
                        },
                        {
                            "title": "Level",
                            "value": alert.level.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        # 添加元数据
        if alert.metadata:
            for key, value in alert.metadata.items():
                payload["attachments"][0]["fields"].append({
                    "title": key.replace("_", " ").title(),
                    "value": str(value),
                    "short": True
                })
        
        # 发送到 Slack
        response = requests.post(
            settings.ALERT_SLACK_WEBHOOK,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """获取最近的告警"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]


# 全局告警管理器
alert_manager = AlertManager()


# 便捷函数
async def send_info_alert(title: str, message: str, **metadata):
    """发送信息级别告警"""
    alert = Alert(title, message, AlertLevel.INFO, metadata=metadata)
    return await alert_manager.send_alert(alert)


async def send_warning_alert(title: str, message: str, **metadata):
    """发送警告级别告警"""
    alert = Alert(title, message, AlertLevel.WARNING, metadata=metadata)
    return await alert_manager.send_alert(alert)


async def send_error_alert(title: str, message: str, **metadata):
    """发送错误级别告警"""
    alert = Alert(title, message, AlertLevel.ERROR, metadata=metadata)
    return await alert_manager.send_alert(alert)


async def send_critical_alert(title: str, message: str, **metadata):
    """发送严重级别告警"""
    alert = Alert(title, message, AlertLevel.CRITICAL, metadata=metadata)
    return await alert_manager.send_alert(alert)


class HealthMonitor:
    """健康监控器"""
    
    def __init__(self):
        self.last_health_status = None
        self.consecutive_failures = 0
        self.max_failures = 3
    
    async def check_and_alert(self, health_result):
        """检查健康状态并发送告警"""
        current_status = health_result.status
        
        # 状态变化告警
        if self.last_health_status and self.last_health_status != current_status:
            if current_status == "unhealthy":
                await send_error_alert(
                    "Service Health Degraded",
                    f"Service status changed from {self.last_health_status} to {current_status}",
                    previous_status=self.last_health_status,
                    current_status=current_status,
                    uptime=health_result.uptime
                )
            elif current_status == "healthy" and self.last_health_status == "unhealthy":
                await send_info_alert(
                    "Service Health Recovered",
                    f"Service status recovered from {self.last_health_status} to {current_status}",
                    previous_status=self.last_health_status,
                    current_status=current_status,
                    uptime=health_result.uptime
                )
        
        # 连续失败告警
        if current_status == "unhealthy":
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures:
                await send_critical_alert(
                    "Service Continuously Unhealthy",
                    f"Service has been unhealthy for {self.consecutive_failures} consecutive checks",
                    consecutive_failures=self.consecutive_failures,
                    uptime=health_result.uptime
                )
        else:
            self.consecutive_failures = 0
        
        # 组件特定告警
        for component in health_result.components:
            if component.status == "unhealthy":
                await send_warning_alert(
                    f"Component {component.name} Unhealthy",
                    component.message or f"Component {component.name} is not healthy",
                    component=component.name,
                    component_status=component.status,
                    response_time=component.response_time
                )
        
        self.last_health_status = current_status


# 全局健康监控器
health_monitor = HealthMonitor()
