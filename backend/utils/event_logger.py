"""
结构化事件日志记录器

为认证事件提供统一的日志记录接口
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from core.auth_events import AuthEvent, AuthEventEmitter, auth_event_emitter


class StructuredEventLogger:
    """
    结构化事件日志记录器
    
    功能：
    - 统一的事件日志格式
    - 文件轮转和保留策略
    - JSON 格式输出便于解析
    """
    
    def __init__(
        self,
        log_dir: str | Path = "logs/auth",
        rotation: str = "10 MB",
        retention: str = "30 days",
    ) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.rotation = rotation
        self.retention = retention
        self._sink_id = None
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """配置结构化日志输出"""
        # 添加 JSON 格式的认证事件日志文件
        self._sink_id = logger.add(
            self.log_dir / "auth_events.jsonl",
            rotation=self.rotation,
            retention=self.retention,
            level="INFO",
            format="{message}",  # JSON 格式，不需要额外格式化
            filter=lambda record: record["extra"].get("is_auth_event") is True,
            serialize=True,  # 输出为 JSON
        )
        
        # 添加人类可读的认证事件日志
        logger.add(
            self.log_dir / "auth_events.log",
            rotation=self.rotation,
            retention=self.retention,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            filter=lambda record: record["extra"].get("is_auth_event") is True,
        )
    
    def log_event(self, event: AuthEvent) -> None:
        """记录认证事件"""
        # 使用 loguru 的 bind 来标记这是认证事件
        auth_logger = logger.bind(is_auth_event=True)
        auth_logger.info(event.to_log_message(), **event.to_dict())
    
    def close(self) -> None:
        """关闭日志记录器"""
        if self._sink_id is not None:
            logger.remove(self._sink_id)


class EventLoggerManager:
    """
    事件日志管理器 - 集中管理事件发射和日志记录
    
    使用方式：
        manager = EventLoggerManager()
        manager.start()
        
        # 使用全局发射器发射事件
        from core.auth_events import auth_event_emitter
        auth_event_emitter.login_succeeded(remote_user_id="123", device_id="abc", auth_state="active")
        
        manager.stop()
    """
    
    def __init__(
        self,
        log_dir: str | Path = "logs/auth",
        emitter: AuthEventEmitter | None = None,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.emitter = emitter or auth_event_emitter
        self._logger: StructuredEventLogger | None = None
        self._started: bool = False
    
    def start(self) -> None:
        """启动事件日志记录"""
        if self._started:
            return
        
        self._logger = StructuredEventLogger(
            log_dir=self.log_dir,
            rotation="10 MB",
            retention="30 days",
        )
        
        # 注册回调以接收所有事件
        self.emitter.register_callback(self._on_event)
        self._started = True
        
        logger.info(f"EventLoggerManager started, logging to {self.log_dir}")
    
    def stop(self) -> None:
        """停止事件日志记录"""
        if not self._started:
            return
        
        # 注销回调
        self.emitter.unregister_callback(self._on_event)
        
        # 关闭日志记录器
        if self._logger:
            self._logger.close()
            self._logger = None
        
        self._started = False
        logger.info("EventLoggerManager stopped")
    
    def _on_event(self, event: AuthEvent) -> None:
        """事件回调 - 记录到文件"""
        if self._logger:
            self._logger.log_event(event)


def setup_auth_event_logging(
    log_dir: str | Path = "logs/auth",
    auto_start: bool = True,
) -> EventLoggerManager:
    """
    设置认证事件日志记录
    
    Args:
        log_dir: 日志文件目录
        auto_start: 是否自动启动
    
    Returns:
        EventLoggerManager 实例
    
    Example:
        manager = setup_auth_event_logging()
        
        # 发射事件
        from core.auth_events import auth_event_emitter
        auth_event_emitter.login_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active"
        )
    """
    manager = EventLoggerManager(log_dir=log_dir)
    if auto_start:
        manager.start()
    return manager


# Convenience function for direct logging
def log_auth_event(
    event_name: str,
    **kwargs: Any,
) -> None:
    """
    直接记录认证事件的便捷函数
    
    Args:
        event_name: 事件名称
        **kwargs: 事件字段 (remote_user_id, device_id, auth_state, reason_code, etc.)
    
    Example:
        log_auth_event(
            "auth_login_succeeded",
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active"
        )
    """
    event = AuthEvent(
        event_name=event_name,
        timestamp=datetime.now(UTC),
        **kwargs,
    )
    
    # 输出到标准日志
    logger.info(event.to_log_message())
    
    # 同时通过发射器分发
    auth_event_emitter.emit(event)
