"""
Phase 5 / PR3: truthful backup artifact tests.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import services.system_backup_service as system_backup_service
import services.system_config_service as system_config_service
from core.config import settings


@pytest.fixture()
def backup_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
  path = tmp_path / "backups"
  monkeypatch.setattr(system_backup_service, "BACKUP_ROOT", path)
  monkeypatch.setattr(system_config_service, "RUNTIME_CONFIG_PATH", tmp_path / "system_config.json")
  return path


@pytest.mark.asyncio
async def test_system_backup_creates_manifest_artifact(client, backup_root: Path) -> None:
  response = await client.post("/api/system/backup", json={"include_logs": False})

  assert response.status_code == 200
  payload = response.json()
  manifest_path = Path(payload["backup_file"])
  assert manifest_path.exists()
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

  assert payload["success"] is True
  assert manifest["effective_system_config"]["material_base_path"] == settings.MATERIAL_BASE_PATH
  assert "database snapshot (when sqlite file exists)" in manifest["backup_scope"]["includes"]
  assert "media files" in manifest["backup_scope"]["excludes"]


@pytest.mark.asyncio
async def test_system_backup_includes_runtime_config_snapshot_when_present(
  client,
  backup_root: Path,
) -> None:
  runtime_config = system_config_service.RUNTIME_CONFIG_PATH
  runtime_config.write_text(json.dumps({"material_base_path": "E:/runtime"}) + "\n", encoding="utf-8")

  response = await client.post("/api/system/backup", json={"include_logs": False})

  assert response.status_code == 200
  manifest = json.loads(Path(response.json()["backup_file"]).read_text(encoding="utf-8"))
  snapshot_path = manifest["artifacts"]["runtime_config_snapshot"]
  assert snapshot_path is not None
  assert Path(snapshot_path).exists()
