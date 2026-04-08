"""
扣子（Coze）API 客户端封装

提供文件上传、工作流提交、状态查询三个核心操作。
"""
import json
from typing import Any

from cozepy import AsyncCoze, AsyncTokenAuth
from loguru import logger

from core.config import settings


class CozeClient:
    """扣子 API 异步客户端封装"""

    def __init__(self) -> None:
        """从 config.settings 读取配置并初始化客户端。

        Raises:
            ValueError: 如果 COZE_API_TOKEN 未配置。
        """
        if not settings.COZE_API_TOKEN:
            raise ValueError("COZE_API_TOKEN 未配置，请在 .env 中设置")

        self._coze = AsyncCoze(
            auth=AsyncTokenAuth(token=settings.COZE_API_TOKEN),
            base_url=settings.COZE_API_BASE,
        )
        logger.info("CozeClient 初始化完成: base_url={}", settings.COZE_API_BASE)

    async def upload_file(self, file_path: str) -> str:
        """上传本地文件到扣子平台。

        Args:
            file_path: 本地文件绝对路径。

        Returns:
            扣子平台返回的 file_id。

        Raises:
            ValueError: COZE_API_TOKEN 未配置。
            Exception: 上传失败时透传 SDK 异常。
        """
        logger.info("开始上传文件: path={}", file_path)
        try:
            file = await self._coze.files.upload(file=file_path)
            logger.info("文件上传成功: file_id={}", file.id)
            return file.id
        except Exception as e:
            logger.error("文件上传失败: path={}, error={}", file_path, str(e))
            raise

    async def submit_composition(
        self, workflow_id: str, parameters: dict[str, Any]
    ) -> str:
        """以异步模式提交工作流执行任务。

        Args:
            workflow_id: 扣子工作流 ID。
            parameters: 传递给工作流的输入参数。

        Returns:
            execute_id，用于后续轮询状态。

        Raises:
            ValueError: COZE_API_TOKEN 未配置。
            Exception: 提交失败时透传 SDK 异常。
        """
        logger.info("提交合成任务: workflow_id={}", workflow_id)
        try:
            result = await self._coze.workflows.runs.create(
                workflow_id=workflow_id,
                is_async=True,
                parameters=parameters,
            )
            logger.info(
                "合成任务提交成功: workflow_id={}, execute_id={}",
                workflow_id,
                result.execute_id,
            )
            return result.execute_id
        except Exception as e:
            logger.error(
                "合成任务提交失败: workflow_id={}, error={}", workflow_id, str(e)
            )
            raise

    async def check_status(
        self, workflow_id: str, execute_id: str
    ) -> tuple[str, dict[str, Any] | None]:
        """查询工作流执行状态。

        Args:
            workflow_id: 扣子工作流 ID。
            execute_id: 由 submit_composition 返回的执行 ID。

        Returns:
            (status, output) 元组：
            - status: WorkflowExecuteStatus 枚举值的字符串表示
              （"running" / "success" / "fail" 等）
            - output: 执行成功时解析后的输出字典；未完成或无输出时为 None。

        Raises:
            ValueError: COZE_API_TOKEN 未配置。
            Exception: 查询失败时透传 SDK 异常。
        """
        logger.debug(
            "查询任务状态: workflow_id={}, execute_id={}", workflow_id, execute_id
        )
        try:
            history = await self._coze.workflows.runs.run_histories.retrieve(
                workflow_id=workflow_id,
                execute_id=execute_id,
            )
            status = str(history.execute_status)
            output: dict[str, Any] | None = None
            if history.output:
                try:
                    output = json.loads(history.output)
                except json.JSONDecodeError as parse_err:
                    logger.warning(
                        "工作流输出 JSON 解析失败: execute_id={}, error={}",
                        execute_id,
                        str(parse_err),
                    )
            logger.debug(
                "任务状态查询完成: execute_id={}, status={}", execute_id, status
            )
            return status, output
        except Exception as e:
            logger.error(
                "任务状态查询失败: execute_id={}, error={}", execute_id, str(e)
            )
            raise
