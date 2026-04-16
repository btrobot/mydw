"""
API 路由初始化
"""
from api import auth
from api import account, task, publish, system, ai, product, video, copywriting, cover, audio, topic, creative

from api import schedule_config

__all__ = ["auth", "account", "task", "publish", "schedule_config", "system", "ai", "product", "video", "copywriting", "cover", "audio", "topic", "creative"]
