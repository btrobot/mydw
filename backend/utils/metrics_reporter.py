"""
????? - Metrics Reporter

????????????????
"""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from core.auth_metrics import AuthMetricsCollector, AuthMetricsSnapshot


class MetricsReporter:
    """
    ?????
    
    ???????????
    """
    
    def __init__(
        self,
        collector: AuthMetricsCollector,
        report_interval_seconds: int = 60,
        output_dir: str | Path = "logs/metrics",
    ) -> None:
        self.collector = collector
        self.report_interval_seconds = report_interval_seconds
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self._callbacks: list[Callable[[AuthMetricsSnapshot], None]] = []
    
    def register_callback(self, callback: Callable[[AuthMetricsSnapshot], None]) -> None:
        """??????"""
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[AuthMetricsSnapshot], None]) -> None:
        """??????"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def start(self) -> None:
        """??????"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._report_loop())
        logger.info(f"MetricsReporter started, interval={self.report_interval_seconds}s")
    
    async def stop(self) -> None:
        """??????"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("MetricsReporter stopped")
    
    async def _report_loop(self) -> None:
        """????"""
        while self._running:
            try:
                await self._report_once()
                await asyncio.sleep(self.report_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics report error: {e}")
                await asyncio.sleep(self.report_interval_seconds)
    
    async def _report_once(self) -> None:
        """??????"""
        snapshot = self.collector.get_snapshot()
        
        # ?????
        self._log_metrics(snapshot)
        
        # ????
        self._write_metrics_file(snapshot)
        
        # ????
        for callback in self._callbacks:
            try:
                callback(snapshot)
            except Exception as e:
                logger.error(f"Metrics callback error: {e}")
    
    def _log_metrics(self, snapshot: AuthMetricsSnapshot) -> None:
        """???????"""
        metrics = snapshot.to_dict()
        logger.info(f"auth_metrics: {json.dumps(metrics, ensure_ascii=False)}")
    
    def _write_metrics_file(self, snapshot: AuthMetricsSnapshot) -> None:
        """???????"""
        timestamp = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"auth_metrics_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)
        
        # ??????????24???
        self._cleanup_old_files()
    
    def _cleanup_old_files(self) -> None:
        """???????"""
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        
        for file in self.output_dir.glob("auth_metrics_*.json"):
            try:
                # ????????
                file_timestamp = datetime.fromtimestamp(
                    file.stat().st_mtime, UTC
                )
                if file_timestamp < cutoff:
                    file.unlink()
            except Exception:
                pass  # ??????
    
    def get_latest_metrics(self) -> dict[str, Any] | None:
        """???????"""
        files = sorted(self.output_dir.glob("auth_metrics_*.json"), reverse=True)
        if not files:
            return None
        
        try:
            with open(files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None


class PrometheusMetricsExporter:
    """
    Prometheus ?????
    
    ?????? Prometheus ??
    """
    
    def __init__(self, collector: AuthMetricsCollector) -> None:
        self.collector = collector
    
    def export(self) -> str:
        """??? Prometheus ??"""
        snapshot = self.collector.get_snapshot()
        lines: list[str] = []
        
        # ????
        lines.append("# HELP auth_login_attempts_total Total login attempts")
        lines.append("# TYPE auth_login_attempts_total counter")
        lines.append(f"auth_login_attempts_total {snapshot.login_attempts_total}")
        
        lines.append("# HELP auth_login_success_total Total successful logins")
        lines.append("# TYPE auth_login_success_total counter")
        lines.append(f"auth_login_success_total {snapshot.login_success_total}")
        
        lines.append("# HELP auth_login_success_rate Login success rate")
        lines.append("# TYPE auth_login_success_rate gauge")
        lines.append(f"auth_login_success_rate {snapshot.login_success_rate}")
        
        lines.append("# HELP auth_refresh_attempts_total Total refresh attempts")
        lines.append("# TYPE auth_refresh_attempts_total counter")
        lines.append(f"auth_refresh_attempts_total {snapshot.refresh_attempts_total}")
        
        lines.append("# HELP auth_refresh_success_rate Refresh success rate")
        lines.append("# TYPE auth_refresh_success_rate gauge")
        lines.append(f"auth_refresh_success_rate {snapshot.refresh_success_rate}")
        
        lines.append("# HELP auth_refresh_avg_latency_ms Average refresh latency")
        lines.append("# TYPE auth_refresh_avg_latency_ms gauge")
        lines.append(f"auth_refresh_avg_latency_ms {snapshot.refresh_avg_latency_ms}")
        
        lines.append("# HELP auth_sessions_current Current sessions by state")
        lines.append("# TYPE auth_sessions_current gauge")
        lines.append(f"auth_sessions_current{{state=\"active\"}} {snapshot.sessions_active}")
        lines.append(f"auth_sessions_current{{state=\"grace\"}} {snapshot.sessions_grace}")
        lines.append(f"auth_sessions_current{{state=\"expired\"}} {snapshot.sessions_expired}")
        lines.append(f"auth_sessions_current{{state=\"revoked\"}} {snapshot.sessions_revoked}")
        lines.append(f"auth_sessions_current{{state=\"unauthenticated\"}} {snapshot.sessions_unauthenticated}")
        
        lines.append("# HELP auth_errors_total Total errors by type")
        lines.append("# TYPE auth_errors_total counter")
        lines.append(f"auth_errors_total{{type=\"network\"}} {snapshot.errors_network_total}")
        lines.append(f"auth_errors_total{{type=\"remote_rejection\"}} {snapshot.errors_remote_rejection_total}")
        lines.append(f"auth_errors_total{{type=\"device_mismatch\"}} {snapshot.errors_device_mismatch_total}")
        
        return "\n".join(lines) + "\n"


def setup_metrics_reporting(
    collector: AuthMetricsCollector,
    report_interval_seconds: int = 60,
) -> MetricsReporter:
    """
    ??????
    
    Args:
        collector: ?????
        report_interval_seconds: ???????
    
    Returns:
        MetricsReporter ??
    """
    reporter = MetricsReporter(
        collector=collector,
        report_interval_seconds=report_interval_seconds,
    )
    return reporter
