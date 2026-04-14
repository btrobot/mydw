"""
远程认证协议适配层。

只负责：
- 调用 remote auth backend
- 解析 Step 0 冻结的 contract
- 映射 transport / response errors

不负责：
- 本地 machine-session 状态机
- secret storage
- AuthService 编排
"""
from __future__ import annotations

from typing import Any

import httpx
from loguru import logger
from pydantic import ValidationError

from core.config import settings
from schemas.auth import (
    RemoteAuthErrorPayload,
    RemoteAuthLogoutPayload,
    RemoteAuthMePayload,
    RemoteAuthSessionPayload,
)


class RemoteAuthClientError(Exception):
    """远程认证客户端基类异常。"""


class RemoteAuthResponseError(RemoteAuthClientError):
    """远程认证返回显式错误响应。"""

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class RemoteAuthTransportError(RemoteAuthClientError):
    """远程 transport 层错误。"""

    def __init__(self, message: str, *, error_code: str = "network_timeout") -> None:
        super().__init__(message)
        self.error_code = error_code


class RemoteAuthProtocolError(RemoteAuthClientError):
    """远程响应不符合冻结协议。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.error_code = "invalid_payload"


class RemoteAuthClient:
    """远程认证客户端。"""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: int | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        resolved_base_url = base_url if base_url is not None else settings.REMOTE_AUTH_BASE_URL
        if not resolved_base_url:
            raise ValueError("REMOTE_AUTH_BASE_URL 未配置，请在 .env 中设置")

        self.base_url = resolved_base_url.rstrip("/")
        self.timeout = timeout if timeout is not None else settings.REMOTE_AUTH_TIMEOUT
        self._external_client = client
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        logger.info("RemoteAuthClient 初始化完成: base_url={}", self.base_url)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def login(
        self,
        *,
        username: str,
        password: str,
        device_id: str,
        client_version: str,
    ) -> RemoteAuthSessionPayload:
        payload = {
            "username": username,
            "password": password,
            "device_id": device_id,
            "client_version": client_version,
        }
        response = await self._post("/login", payload, event_name="auth_login")
        parsed = self._parse_success_payload(response, RemoteAuthSessionPayload)
        logger.info("event_name=auth_login_succeeded remote_user_id={}", parsed.user.id)
        return parsed

    async def refresh(
        self,
        *,
        refresh_token: str,
        device_id: str,
        client_version: str,
    ) -> RemoteAuthSessionPayload:
        payload = {
            "refresh_token": refresh_token,
            "device_id": device_id,
            "client_version": client_version,
        }
        response = await self._post("/refresh", payload, event_name="auth_refresh")
        parsed = self._parse_success_payload(response, RemoteAuthSessionPayload)
        logger.info("event_name=auth_refresh_succeeded remote_user_id={}", parsed.user.id)
        return parsed

    async def logout(
        self,
        *,
        refresh_token: str,
        device_id: str,
    ) -> RemoteAuthLogoutPayload:
        payload = {
            "refresh_token": refresh_token,
            "device_id": device_id,
        }
        response = await self._post("/logout", payload, event_name="auth_logout")
        parsed = self._parse_success_payload(response, RemoteAuthLogoutPayload)
        return parsed

    async def me(self, *, access_token: str) -> RemoteAuthMePayload:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request("GET", "/me", headers=headers, event_name="auth_me")
        parsed = self._parse_success_payload(response, RemoteAuthMePayload)
        return parsed

    async def _post(self, path: str, payload: dict[str, Any], *, event_name: str) -> httpx.Response:
        return await self._request("POST", path, json=payload, event_name=event_name)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        event_name: str,
    ) -> httpx.Response:
        try:
            response = await self._client.request(method, path, json=json, headers=headers)
        except httpx.TimeoutException as exc:
            logger.warning("event_name={}_failed error_code=network_timeout", event_name)
            raise RemoteAuthTransportError("远程认证请求超时") from exc
        except httpx.HTTPError as exc:
            logger.warning("event_name={}_failed error_code=network_timeout", event_name)
            raise RemoteAuthTransportError("远程认证请求失败") from exc

        if response.status_code >= 400:
            error = self._parse_error_payload(response)
            self._log_error_event(event_name, error.error_code)
            raise RemoteAuthResponseError(
                error.error_code,
                error.message,
                status_code=response.status_code,
                details=error.details,
            )

        return response

    @staticmethod
    def _parse_success_payload(response: httpx.Response, model: type[RemoteAuthSessionPayload | RemoteAuthMePayload | RemoteAuthLogoutPayload]):
        try:
            data = response.json()
        except ValueError as exc:
            raise RemoteAuthProtocolError("远程认证响应不是合法 JSON") from exc

        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise RemoteAuthProtocolError(f"远程认证响应不符合冻结协议: {exc}") from exc

    @staticmethod
    def _parse_error_payload(response: httpx.Response) -> RemoteAuthErrorPayload:
        try:
            data = response.json()
        except ValueError as exc:
            raise RemoteAuthProtocolError("远程认证错误响应不是合法 JSON") from exc

        try:
            return RemoteAuthErrorPayload.model_validate(data)
        except ValidationError as exc:
            raise RemoteAuthProtocolError(f"远程认证错误响应不符合冻结协议: {exc}") from exc

    @staticmethod
    def _log_error_event(event_name: str, error_code: str) -> None:
        if error_code == "revoked":
            logger.warning("event_name=auth_revoked source_event={}", event_name)
        elif error_code == "device_mismatch":
            logger.warning("event_name=auth_device_mismatch source_event={}", event_name)
        elif error_code == "token_expired":
            logger.warning("event_name=auth_refresh_failed source_event={} error_code=token_expired", event_name)
        else:
            logger.warning("event_name={}_failed error_code={}", event_name, error_code)

