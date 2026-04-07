"""
得物掘金工具 - 素材库种子数据脚本

用法:
    python -m backend.seeds

幂等: 先清空素材相关表再插入，重复运行安全。
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 确保 backend 目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from loguru import logger

from models import (
    Base,
    Product,
    Video,
    Copywriting,
    Cover,
    Audio,
    Topic,
)
from core.config import settings


# ---------------------------------------------------------------------------
# 种子数据定义
# ---------------------------------------------------------------------------

PRODUCTS = [
    {
        "name": "耐克Air Max 270 黑白配色运动鞋",
        "link": "https://www.dewu.com/product/12345",
        "description": "经典黑白配色，Air Max气垫，全天候舒适穿着体验",
        "dewu_url": "https://www.dewu.com/product/12345",
        "image_url": "https://cdn.dewu.com/images/12345.jpg",
    },
    {
        "name": "阿迪达斯Yeezy Boost 350 V2 斑马",
        "link": "https://www.dewu.com/product/23456",
        "description": "Kanye West联名款，Boost底科技，限量发售",
        "dewu_url": "https://www.dewu.com/product/23456",
        "image_url": "https://cdn.dewu.com/images/23456.jpg",
    },
    {
        "name": "Supreme x The North Face 联名冲锋衣",
        "link": "https://www.dewu.com/product/34567",
        "description": "Supreme联名北面，防风防水，街头潮流必备单品",
        "dewu_url": "https://www.dewu.com/product/34567",
        "image_url": "https://cdn.dewu.com/images/34567.jpg",
    },
    {
        "name": "Jordan 1 Retro High OG 芝加哥",
        "link": "https://www.dewu.com/product/45678",
        "description": "AJ1芝加哥配色，经典复刻，篮球文化图腾",
        "dewu_url": "https://www.dewu.com/product/45678",
        "image_url": "https://cdn.dewu.com/images/45678.jpg",
    },
    {
        "name": "古驰GG Marmont 绗缝皮革单肩包",
        "link": "https://www.dewu.com/product/56789",
        "description": "Gucci经典款，绗缝皮革工艺，双G金属扣，奢华时尚",
        "dewu_url": "https://www.dewu.com/product/56789",
        "image_url": "https://cdn.dewu.com/images/56789.jpg",
    },
]

# 每个商品对应的视频列表（按 PRODUCTS 顺序）
VIDEOS_BY_PRODUCT: list[list[dict]] = [
    # 商品0: 耐克Air Max 270
    [
        {
            "name": "耐克AirMax270开箱评测",
            "file_path": "D:/素材库/耐克AirMax270/开箱评测_01.mp4",
            "file_size": 158_000_000,
            "duration": 62,
            "width": 1080,
            "height": 1920,
            "file_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
            "source_type": "original",
        },
        {
            "name": "耐克AirMax270上脚展示",
            "file_path": "D:/素材库/耐克AirMax270/上脚展示_02.mp4",
            "file_size": 92_000_000,
            "duration": 38,
            "width": 1080,
            "height": 1920,
            "file_hash": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
            "source_type": "original",
        },
        {
            "name": "耐克AirMax270细节特写",
            "file_path": "D:/素材库/耐克AirMax270/细节特写_03.mp4",
            "file_size": 74_000_000,
            "duration": 29,
            "width": 1080,
            "height": 1920,
            "file_hash": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
            "source_type": "clip",
        },
    ],
    # 商品1: Yeezy 350 V2
    [
        {
            "name": "Yeezy350V2斑马开箱",
            "file_path": "D:/素材库/Yeezy350V2/斑马开箱_01.mp4",
            "file_size": 201_000_000,
            "duration": 85,
            "width": 1080,
            "height": 1920,
            "file_hash": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1",
            "source_type": "original",
        },
        {
            "name": "Yeezy350V2真假对比",
            "file_path": "D:/素材库/Yeezy350V2/真假对比_02.mp4",
            "file_size": 135_000_000,
            "duration": 55,
            "width": 1080,
            "height": 1920,
            "file_hash": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            "source_type": "original",
        },
    ],
    # 商品2: Supreme x TNF 冲锋衣
    [
        {
            "name": "Supreme北面联名冲锋衣开箱",
            "file_path": "D:/素材库/SupremeTNF/冲锋衣开箱_01.mp4",
            "file_size": 178_000_000,
            "duration": 72,
            "width": 1080,
            "height": 1920,
            "file_hash": "f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
            "source_type": "original",
        },
        {
            "name": "Supreme北面穿搭上身效果",
            "file_path": "D:/素材库/SupremeTNF/穿搭上身_02.mp4",
            "file_size": 110_000_000,
            "duration": 45,
            "width": 1080,
            "height": 1920,
            "file_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d5",
            "source_type": "clip",
        },
        {
            "name": "Supreme北面防水测试",
            "file_path": "D:/素材库/SupremeTNF/防水测试_03.mp4",
            "file_size": 88_000_000,
            "duration": 33,
            "width": 1080,
            "height": 1920,
            "file_hash": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4f7",
            "source_type": "original",
        },
    ],
    # 商品3: AJ1 芝加哥
    [
        {
            "name": "AJ1芝加哥开箱鉴定",
            "file_path": "D:/素材库/AJ1Chicago/开箱鉴定_01.mp4",
            "file_size": 245_000_000,
            "duration": 98,
            "width": 1080,
            "height": 1920,
            "file_hash": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5a8",
            "source_type": "original",
        },
        {
            "name": "AJ1芝加哥上脚街拍",
            "file_path": "D:/素材库/AJ1Chicago/上脚街拍_02.mp4",
            "file_size": 167_000_000,
            "duration": 67,
            "width": 1080,
            "height": 1920,
            "file_hash": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6b9",
            "source_type": "original",
        },
    ],
    # 商品4: Gucci GG Marmont
    [
        {
            "name": "古驰GGMarmont开箱展示",
            "file_path": "D:/素材库/GucciGGMarmont/开箱展示_01.mp4",
            "file_size": 192_000_000,
            "duration": 78,
            "width": 1080,
            "height": 1920,
            "file_hash": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1c0",
            "source_type": "original",
        },
        {
            "name": "古驰GGMarmont搭配穿搭",
            "file_path": "D:/素材库/GucciGGMarmont/搭配穿搭_02.mp4",
            "file_size": 143_000_000,
            "duration": 58,
            "width": 1080,
            "height": 1920,
            "file_hash": "f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2d1",
            "source_type": "clip",
        },
        {
            "name": "古驰GGMarmont细节工艺",
            "file_path": "D:/素材库/GucciGGMarmont/细节工艺_03.mp4",
            "file_size": 98_000_000,
            "duration": 41,
            "width": 1080,
            "height": 1920,
            "file_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3e2",
            "source_type": "original",
        },
    ],
]

# 每个商品对应的文案列表（按 PRODUCTS 顺序）
COPYWRITINGS_BY_PRODUCT: list[list[dict]] = [
    # 商品0: 耐克Air Max 270
    [
        {"content": "黑白经典，永不过时！耐克Air Max 270这双鞋真的绝了，Air气垫踩上去像踩云朵，全天站立也不累脚。黑白配色百搭，无论是运动还是日常穿都超帅！#耐克 #AirMax #球鞋", "source_type": "manual"},
        {"content": "开箱分享！这双耐克AirMax270黑白配色，鞋面材质很扎实，气垫回弹感超强。穿了一周了，脚感越来越好，强烈推荐给喜欢运动风的朋友们！", "source_type": "manual"},
        {"content": "Air Max 270，270度可视气垫，这个设计真的太酷了！黑白配色经典百搭，上脚效果非常好看。得物正品保障，放心入手！", "source_type": "ai"},
        {"content": "运动鞋天花板！耐克Air Max 270黑白款，轻量化设计，长时间穿着不累脚。无论是健身、跑步还是日常通勤，这双鞋都能完美胜任！", "source_type": "ai"},
        {"content": "球鞋控必入！AirMax270这个系列一直是我的最爱，黑白配色最经典，搭配什么都好看。气垫脚感一流，性价比超高！", "source_type": "manual"},
    ],
    # 商品1: Yeezy 350 V2
    [
        {"content": "Yeezy 350 V2斑马配色，这个颜色真的太好看了！Boost底科技加持，脚感软弹，穿着舒适度满分。限量款，得物有货赶紧入！#Yeezy #椰子鞋", "source_type": "manual"},
        {"content": "开箱Yeezy Boost 350 V2斑马！黑白条纹设计超有辨识度，Primeknit鞋面包裹感极佳，Boost中底回弹感超强。这双鞋值得每个球鞋爱好者拥有！", "source_type": "manual"},
        {"content": "椰子鞋天花板！Yeezy 350 V2斑马配色，经典中的经典。Boost科技让每一步都充满弹性，穿着体验无与伦比。正品保障，放心购！", "source_type": "ai"},
        {"content": "Kanye联名款，斑马配色Yeezy 350 V2，这双鞋的设计感真的无敌！无论是搭配休闲装还是运动装都超好看，球鞋控必备！", "source_type": "crawl", "source_ref": "https://weibo.com/post/12345"},
    ],
    # 商品2: Supreme x TNF 冲锋衣
    [
        {"content": "Supreme x The North Face联名冲锋衣，这个联名真的太强了！防风防水性能一流，Supreme的logo设计超有辨识度。街头潮流必备单品！#Supreme #北面", "source_type": "manual"},
        {"content": "开箱Supreme北面联名冲锋衣！面料质感超好，防水涂层处理很到位，下雨天穿完全不用担心。Supreme的红色logo点缀，整体设计感满分！", "source_type": "manual"},
        {"content": "潮流与功能的完美结合！Supreme x TNF联名冲锋衣，既有街头潮牌的设计感，又有北面的专业户外性能。这件衣服真的值得入手！", "source_type": "ai"},
        {"content": "Supreme联名款，每次发售都是秒空！这次北面联名冲锋衣，防风防水，保暖性能出色。得物正品，限量发售，手慢无！", "source_type": "crawl", "source_ref": "https://xiaohongshu.com/post/67890"},
        {"content": "冬天必备！Supreme x The North Face冲锋衣，穿上就是街头最靓的仔。面料厚实，保暖效果极佳，设计感十足！", "source_type": "manual"},
    ],
    # 商品3: AJ1 芝加哥
    [
        {"content": "AJ1芝加哥配色，篮球文化的图腾！这双鞋的历史地位无可撼动，红白黑三色经典搭配，上脚效果帅到爆炸。得物正品鉴定，放心入手！#AJ1 #乔丹", "source_type": "manual"},
        {"content": "开箱Jordan 1 Retro High OG芝加哥！这双鞋真的是球鞋史上最经典的配色之一，皮革质感超好，鞋型完美。穿上它就是行走的艺术品！", "source_type": "manual"},
        {"content": "球鞋之王！AJ1芝加哥配色，1985年首发至今依然是最受欢迎的配色。复刻版做工精良，皮革质感一流，值得每个球鞋爱好者收藏！", "source_type": "ai"},
        {"content": "芝加哥配色AJ1，这双鞋承载了太多篮球文化的记忆。Michael Jordan的传奇，通过这双鞋得以延续。正品保障，球鞋控必入！", "source_type": "ai"},
    ],
    # 商品4: Gucci GG Marmont
    [
        {"content": "古驰GG Marmont绗缝单肩包，奢华与优雅的完美结合！双G金属扣设计超有辨识度，皮革质感一流，容量适中，日常出行完全够用。#Gucci #古驰", "source_type": "manual"},
        {"content": "开箱Gucci GG Marmont！绗缝皮革工艺精湛，双G金属扣闪闪发光，内里空间合理。这款包真的是奢侈品入门首选，百搭又有品位！", "source_type": "manual"},
        {"content": "时尚界的经典之作！Gucci GG Marmont绗缝皮革单肩包，精湛的意大利工艺，标志性的双G设计，彰显品位与格调。得物正品保障！", "source_type": "ai"},
        {"content": "古驰经典款，GG Marmont系列永远不会过时！绗缝皮革质感超好，双G扣设计精美，搭配任何穿搭都能提升整体气质。值得投资的一款包！", "source_type": "crawl", "source_ref": "https://weibo.com/post/99999"},
        {"content": "奢品入门首选！Gucci GG Marmont，经典绗缝设计，精致双G金属扣，皮革质感细腻。无论是日常通勤还是约会出行，这款包都是完美选择！", "source_type": "manual"},
    ],
]

AUDIOS = [
    {
        "name": "轻快流行BGM-活力四射",
        "file_path": "D:/素材库/音频/BGM/轻快流行_活力四射.mp3",
        "file_size": 8_500_000,
        "duration": 180,
    },
    {
        "name": "电子舞曲BGM-潮流节拍",
        "file_path": "D:/素材库/音频/BGM/电子舞曲_潮流节拍.mp3",
        "file_size": 9_200_000,
        "duration": 195,
    },
    {
        "name": "嘻哈说唱BGM-街头风格",
        "file_path": "D:/素材库/音频/BGM/嘻哈说唱_街头风格.mp3",
        "file_size": 7_800_000,
        "duration": 165,
    },
    {
        "name": "轻音乐BGM-温柔治愈",
        "file_path": "D:/素材库/音频/BGM/轻音乐_温柔治愈.mp3",
        "file_size": 10_100_000,
        "duration": 210,
    },
    {
        "name": "国风BGM-东方韵味",
        "file_path": "D:/素材库/音频/BGM/国风_东方韵味.mp3",
        "file_size": 8_900_000,
        "duration": 188,
    },
]

TOPICS = [
    {"name": "球鞋开箱", "heat": 9800000, "source": "crawl"},
    {"name": "潮流穿搭", "heat": 15600000, "source": "crawl"},
    {"name": "得物好物推荐", "heat": 12300000, "source": "crawl"},
    {"name": "耐克Nike", "heat": 8700000, "source": "crawl"},
    {"name": "Yeezy椰子鞋", "heat": 7200000, "source": "crawl"},
    {"name": "Supreme潮牌", "heat": 6500000, "source": "manual"},
    {"name": "AJ乔丹", "heat": 11400000, "source": "crawl"},
    {"name": "奢侈品开箱", "heat": 5300000, "source": "manual"},
    {"name": "Gucci古驰", "heat": 4800000, "source": "manual"},
    {"name": "限量球鞋", "heat": 9100000, "source": "crawl"},
]


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

async def clear_material_tables(session: AsyncSession) -> None:
    """清空素材相关表（保留账号和任务数据）"""
    # 按外键依赖顺序删除
    await session.execute(delete(Cover))
    await session.execute(delete(Video))
    await session.execute(delete(Copywriting))
    await session.execute(delete(Audio))
    await session.execute(delete(Topic))
    await session.execute(delete(Product))
    await session.commit()
    logger.info("素材表已清空")


async def seed(session: AsyncSession) -> None:
    """插入所有种子数据"""
    now = datetime.utcnow()

    # 1. 商品
    product_objs: list[Product] = []
    for i, p in enumerate(PRODUCTS):
        obj = Product(
            **p,
            created_at=now - timedelta(days=30 - i * 5),
            updated_at=now,
        )
        session.add(obj)
        product_objs.append(obj)

    await session.flush()  # 获取自增 ID
    logger.info("已插入 {} 个商品", len(product_objs))

    # 2. 视频 + 封面
    video_count = 0
    cover_count = 0
    for product_obj, video_list in zip(product_objs, VIDEOS_BY_PRODUCT):
        for j, v in enumerate(video_list):
            video_obj = Video(
                product_id=product_obj.id,
                created_at=now - timedelta(days=25 - j * 3),
                updated_at=now,
                **v,
            )
            session.add(video_obj)
            await session.flush()

            # 每个视频生成 1 张封面
            cover_obj = Cover(
                video_id=video_obj.id,
                file_path=v["file_path"].replace(".mp4", "_cover.jpg"),
                file_size=350_000 + j * 50_000,
                width=1080,
                height=1920,
                created_at=now - timedelta(days=24 - j * 3),
            )
            session.add(cover_obj)
            video_count += 1
            cover_count += 1

    logger.info("已插入 {} 个视频，{} 张封面", video_count, cover_count)

    # 3. 文案
    cw_count = 0
    for product_obj, cw_list in zip(product_objs, COPYWRITINGS_BY_PRODUCT):
        for k, cw in enumerate(cw_list):
            cw_obj = Copywriting(
                product_id=product_obj.id,
                created_at=now - timedelta(days=20 - k * 2),
                updated_at=now,
                **cw,
            )
            session.add(cw_obj)
            cw_count += 1

    logger.info("已插入 {} 条文案", cw_count)

    # 4. 音频
    for m, a in enumerate(AUDIOS):
        audio_obj = Audio(
            created_at=now - timedelta(days=15 - m * 2),
            **a,
        )
        session.add(audio_obj)

    logger.info("已插入 {} 个音频", len(AUDIOS))

    # 5. 话题
    for n, t in enumerate(TOPICS):
        topic_obj = Topic(
            last_synced=now - timedelta(hours=n * 6),
            created_at=now - timedelta(days=10 - n),
            **t,
        )
        session.add(topic_obj)

    logger.info("已插入 {} 个话题", len(TOPICS))

    await session.commit()
    logger.info("种子数据写入完成")


async def main() -> None:
    logger.info("开始写入种子数据，数据库: {}", settings.DATABASE_URL)

    # 确保 data 目录存在
    Path("data").mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        await clear_material_tables(session)
        await seed(session)

    await engine.dispose()
    logger.info("种子数据脚本执行完毕")


if __name__ == "__main__":
    asyncio.run(main())
