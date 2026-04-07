"""
任务发布服务
"""
import asyncio
from typing import Optional, List
from datetime import datetime, time
from zoneinfo import ZoneInfo
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from models import Task, Account, PublishLog, PublishConfig, Product
from core.browser import browser_manager
from core.dewu_client import get_dewu_client


class PublishService:
    """发布服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.is_running = False
        self.is_paused = False
        self.current_task_id: Optional[int] = None

    async def get_config(self) -> PublishConfig:
        """获取发布配置"""
        result = await self.db.execute(
            select(PublishConfig).where(PublishConfig.name == "default")
        )
        config = result.scalar_one_or_none()

        if not config:
            config = PublishConfig(name="default")
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)

        return config

    async def get_next_task(self) -> Optional[Task]:
        """获取下一个待发布任务"""
        # 检查是否在允许的时间范围内
        config = await self.get_config()
        now = datetime.now(ZoneInfo("Asia/Shanghai")).time()

        start_time = time(config.start_hour)
        end_time = time(config.end_hour)

        if not (start_time <= now <= end_time):
            logger.info("当前时间 {} 不在发布时段 {}-{} 内", now, start_time, end_time)
            return None

        # 获取待发布任务
        query = select(Task).where(Task.status == "pending")
        query = query.order_by(Task.priority.desc(), Task.created_at)
        query = query.limit(1)

        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if task:
            # 检查账号当日发布数
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await self.db.execute(
                select(Task).where(
                    Task.account_id == task.account_id,
                    Task.status == "success",
                    Task.updated_at >= today_start
                )
            )
            published_today = len(result.scalars().all())

            if published_today >= config.max_per_account_per_day:
                logger.info("账号 {} 今日发布数已达上限", task.account_id)
                task.status = "paused"
                await self.db.commit()
                return None

        return task

    async def publish_task(self, task: Task) -> tuple[bool, str]:
        """发布单个任务"""
        self.current_task_id = task.id

        try:
            # 更新任务状态
            task.status = "running"
            await self.db.commit()

            # 重新查询 task，预加载所有关系（传入的 task 可能未加载关系）
            task_result = await self.db.execute(
                select(Task).options(
                    selectinload(Task.video),
                    selectinload(Task.copywriting),
                    selectinload(Task.audio),
                    selectinload(Task.product),
                    selectinload(Task.topics),
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
                task.status = "failed"
                task.error_msg = "账号无效或未登录"
                await self.db.commit()
                return False, "账号无效"

            # 创建发布日志
            log = PublishLog(
                task_id=task.id,
                account_id=account.id,
                status="started",
                message="开始发布"
            )
            self.db.add(log)
            await self.db.commit()

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
                task.status = "failed"
                task.error_msg = "登录已过期"
                await self.db.commit()
                return False, "登录已过期"

            # 读取素材字段（FK优先，fallback旧字段）
            video_path: Optional[str] = (
                task.video.file_path if task.video else task.video_path
            )
            content: str = (
                task.copywriting.content if task.copywriting else task.content or ""
            )
            topic: Optional[str] = (
                ", ".join(t.name for t in task.topics) if task.topics else task.topic
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
                cover_path=task.cover_path,
                product_link=product_link
            )

            if success:
                task.status = "success"
                task.publish_time = datetime.utcnow()
                task.error_msg = None

                # 更新日志
                log.status = "success"
                log.message = "发布成功"
                await self.db.commit()

                logger.info("任务 {} 发布成功", task.id)
                return True, "发布成功"
            else:
                task.status = "failed"
                task.error_msg = msg

                log.status = "failed"
                log.message = msg
                await self.db.commit()

                logger.error("任务 {} 发布失败: {}", task.id, msg)
                return False, msg

        except Exception as e:
            logger.error("发布任务 {} 异常: {}", task.id, e)
            task.status = "failed"
            task.error_msg = str(e)
            await self.db.commit()
            return False, str(e)

        finally:
            self.current_task_id = None

    async def run(self):
        """运行发布循环"""
        if self.is_running:
            logger.warning("发布服务已在运行")
            return

        self.is_running = True
        self.is_paused = False
        logger.info("发布服务启动")

        try:
            config = await self.get_config()

            while self.is_running:
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue

                # 获取下一个任务
                task = await self.get_next_task()

                if not task:
                    # 没有待发布任务，等待后重试
                    await asyncio.sleep(10)
                    continue

                # 发布任务
                await self.publish_task(task)

                # 等待间隔
                interval = config.interval_minutes * 60
                logger.info("等待 {} 分钟后继续...", config.interval_minutes)
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("发布服务已取消")
        except Exception as e:
            logger.error("发布服务异常: {}", e)
        finally:
            self.is_running = False
            logger.info("发布服务停止")

    def pause(self):
        """暂停发布"""
        self.is_paused = True
        logger.info("发布已暂停")

    def resume(self):
        """继续发布"""
        self.is_paused = False
        logger.info("发布已继续")

    def stop(self):
        """停止发布"""
        self.is_running = False
        self.is_paused = False
        logger.info("发布已停止")


def get_publish_service(db: AsyncSession) -> PublishService:
    """获取发布服务实例"""
    return PublishService(db)
