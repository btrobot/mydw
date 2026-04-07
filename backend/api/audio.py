"""
得物掘金工具 - 音频管理 API (SP1-04, SP8-03)
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models import Audio, get_db
from schemas import AudioResponse
from core.config import settings
from utils.ffprobe import extract_video_metadata

router = APIRouter(tags=["音频管理"])

AUDIO_DIR = Path(settings.MATERIAL_BASE_PATH) / "audio"

ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/aac", "audio/ogg"}
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("/upload", response_model=AudioResponse, status_code=201)
async def upload_audio(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> AudioResponse:
    """上传音频文件"""
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持 MP3/WAV/AAC/OGG")

    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，最大支持 100MB")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.replace("..", "")
    file_path = AUDIO_DIR / safe_name

    try:
        file_path.write_bytes(content)
    except Exception as e:
        logger.error("音频文件写入失败: filename={}, error={}", safe_name, str(e))
        raise HTTPException(status_code=500, detail="文件保存失败")

    audio = Audio(
        name=safe_name,
        file_path=str(file_path),
        file_size=len(content),
    )
    # SP8-03: FFprobe 提取音频时长
    meta = await extract_video_metadata(str(file_path))
    audio.duration = meta.duration
    db.add(audio)
    await db.commit()
    await db.refresh(audio)
    logger.info("音频上传成功: audio_id={}, filename={}", audio.id, safe_name)
    return audio


@router.get("", response_model=list[AudioResponse])
async def list_audios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[AudioResponse]:
    """获取音频列表（支持分页）"""
    result = await db.execute(
        select(Audio).order_by(Audio.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.delete("/{audio_id}", status_code=204)
async def delete_audio(
    audio_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除音频"""
    result = await db.execute(select(Audio).where(Audio.id == audio_id))
    audio = result.scalars().first()
    if not audio:
        raise HTTPException(status_code=404, detail="音频不存在")

    if audio.file_path:
        file_path = Path(audio.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning("音频文件删除失败: audio_id={}, error={}", audio_id, str(e))

    await db.delete(audio)
    await db.commit()
    logger.info("音频删除成功: audio_id={}", audio_id)
