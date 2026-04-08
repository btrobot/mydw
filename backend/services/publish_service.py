"""
任务发布服务
"""
from typing import Optional
from datetime import datetime, time
from zoneinfo import ZoneInfo
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Task, Account, ScheduleConfig, Product
from core.browser import browser_manager
from core.dewu_client import get_dewu_client
from services.task_service import TaskService


class PublishService:
    """发布服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.current_task_id: Optional[int] = None

    async def _get_schedule_config(self) -> Optional[ScheduleConfig]:
        """从 schedule_config 表读取 name=default 配置"""
        result = await self.db.execute(
            select(ScheduleConfig).where(ScheduleConfig.name == "default")
        )
        return result.scalar_one_or_none()

    async def get_next_task(self) -> Optional[Task]:
        """获取下一个 ready 状态任务（含时段和日限额检查）"""
        config = await self._get_schedule_config()
        now = datetime.now(ZoneInfo("Asia/Shanghai")).time()

        if config:
            start_time = time(config.start_hour)
            end_time = time(config.end_hour)
            if not (start_time <= now <= end_time):
                logger.info("当前时间 {} 不在发布时段 {}-{} 内", now, start_time, end_time)
                return None

        # 查询 status=ready 的任务
        query = (
            select(Task)
            .where(Task.status == "ready")
            .order_by(Task.priority.desc(), Task.created_at)
            .limit(1)
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if task and config:
            # 检查账号当日 uploaded 数量
            task_svc = TaskService(self.db)
            limit_reached = await task_svc.check_account_daily_limit(
                task.account_id, config.max_per_account_per_day
            )
            if limit_reached:
                logger.info("账号 {} 今日发布数已达上限", task.account_id)
                return None

        return task

    async def publish_task(self, task: Task) -> tuple[bool, str]:
        """发布单个任务"""
        self.current_task_id = task.id
        task_svc = TaskService(self.db)

        try:
            # 标记为上传中
            await task_svc.mark_task_uploading(task.id)

            # 重新查询并预加载所有关系
            task_result = await self.db.execute(
                select(Task).options(
                    selectinload(Task.video),
                    selectinload(Task.copywriting),
                    selectinload(Task.audio),
                    selectinload(Task.product),
                    selectinload(Task.topics),
                    selectinload(Task.cover),
                ).where(Task.id == task.id)
            )
            task = task_result.scalar_one_or_none()
            if not task:
                return False, "任务不存在"

            # 获取账号
            result = await self.db.execute(
                select(Account).where(Account.id == task.account_id)
            )
            account = result.scalar_one_or_none()

            if not account or account.status != "active":
                await task_svc.mark_task_failed(task.id, "账号无效或未登录")
                return False, "账号无效"

            # 获取得物客户端
            client = await get_dewu_client(account.id)

            # 尝试使用现有上下文或创建新上下文
            context = await browser_manager.get_or_create_context(
                account.id,
                account.storage_state
            )

            if context and context.pages:
                client.page = context.pages[0]
            else:
                client.page = await browser_manager.new_page(account.id)

            # 检查登录状态
            is_logged_in, msg = await client.check_login_status()
            if not is_logged_in:
                await task_svc.mark_task_failed(task.id, "登录已过期")
                return False, "登录已过期"

            # 读取素材字段
            video_path: Optional[str] = (
                task.video.file_path if task.video else None
            )
            content: str = (
                task.copywriting.content if task.copywriting else ""
            )
            topic: Optional[str] = (
                ", ".join(t.name for t in task.topics) if task.topics else None
            )

            # 读取商品链接（product 关系已预加载，fallback 到单独查询）
            product_link: Optional[str] = None
            if task.product:
                product_link = task.product.link
            elif task.product_id:
                prod_result = await self.db.execute(
                    select(Product).where(Product.id == task.product_id)
                )
                product = prod_result.scalar_one_or_none()
                if product:
                    product_link = product.link

            # 发布视频
            success, msg = await client.upload_video(
                video_path=video_path,
                title=content[:50] if content else "视频标题",
                content=content,
                topic=topic,
                cover_path=task.cover.file_path if task.cover else None,
                product_link=product_link
            )

            if success:
                await task_svc.mark_task_uploaded(task.id)
                logger.info("任务 {} 发布成功", task.id)
                return True, "发布成功"
            else:
                await task_svc.mark_task_failed(task.id, msg)
                logger.error("任务 {} 发布失败: {}", task.id, msg)
                return False, msg

        except Exception as e:
            logger.error("发布任务 {} 异常: {}", task.id, e)
            await task_svc.mark_task_failed(task.id, str(e))
            return False, str(e)

        finally:
            self.current_task_id = None


def get_publish_service(db: AsyncSession) -> PublishService:
    """获取发布服务实例"""
    return PublishService(db)
