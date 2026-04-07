# 常用模式速查

## 后端模式 (Python FastAPI)

### API 路由模板

```python
@router.post("/", response_model=XxxResponse, status_code=201)
async def create_xxx(
    data: XxxCreate,
    db: AsyncSession = Depends(get_db),
) -> XxxResponse:
    """创建 XXX"""
    result = await xxx_service.create(db, data)
    return result
```

### Service 方法模板

```python
async def create(db: AsyncSession, data: XxxCreate) -> Xxx:
    """
    创建 XXX
    
    Args:
        db: 数据库会话
        data: 创建请求数据 (Pydantic Schema)
    
    Returns:
        创建的实体对象
    
    Raises:
        HTTPException(400): 参数校验失败
        HTTPException(404): 关联实体不存在
    """
    # 1. 业务校验
    # 2. 创建实体
    obj = Xxx(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
```

### 加密存储模式

```python
from utils.crypto import encrypt_data, decrypt_data, mask_phone

# 存储时加密
account.cookie = encrypt_data(raw_cookie)
account.phone_encrypted = encrypt_data(phone_number)

# 读取时解密
raw_cookie = decrypt_data(account.cookie)

# 日志中脱敏
logger.info(f"账号 {account.account_name} 手机号: {mask_phone(phone)}")
```

### Patchright 浏览器操作模式

```python
async with browser_manager.get_context(account) as context:
    page = await context.new_page()
    try:
        await page.goto("https://creator.dewu.com/")
        # ... 自动化操作
    finally:
        await page.close()
```

### 异步数据库查询模式

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 带关联加载的查询
stmt = (
    select(Task)
    .options(selectinload(Task.video), selectinload(Task.copywriting))
    .where(Task.status == "pending")
    .order_by(Task.priority.desc(), Task.created_at)
    .offset(skip)
    .limit(limit)
)
result = await db.execute(stmt)
tasks = result.scalars().all()
```

### SSE 事件推送模式

```python
from sse_starlette.sse import EventSourceResponse

@router.get("/connect/{account_id}/stream")
async def connection_stream(account_id: int):
    async def event_generator():
        while True:
            status = connection_manager.get_status(account_id)
            yield {"event": "status", "data": json.dumps(status)}
            if status.get("stage") in ("done", "error"):
                break
            await asyncio.sleep(1)
    return EventSourceResponse(event_generator())
```

### FFmpeg 子进程调用模式

```python
import subprocess

cmd = [
    "ffmpeg", "-y",
    "-i", input_path,
    "-ss", str(start),
    "-to", str(end),
    "-c:v", "libx264",
    "-c:a", "aac",
    output_path,
]
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=300,  # 5 分钟超时
)
if result.returncode != 0:
    logger.error(f"FFmpeg 失败: {result.stderr}")
    raise HTTPException(500, detail="视频处理失败")
```

---

## 前端模式 (React + TypeScript)

### 页面组件模板

```tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Button, message } from "antd";

export default function XxxPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["xxx"],
    queryFn: () => api.getXxxList(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteXxx(id),
    onSuccess: () => {
      message.success("删除成功");
      queryClient.invalidateQueries({ queryKey: ["xxx"] });
    },
  });

  return <Table dataSource={data?.items} loading={isLoading} />;
}
```

### React Query Hook 封装模式

```tsx
// hooks/useXxx.ts
export function useXxxList(params?: XxxListParams) {
  return useQuery({
    queryKey: ["xxx", params],
    queryFn: () => api.getXxxList(params),
  });
}

export function useCreateXxx() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: XxxCreate) => api.createXxx(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["xxx"] });
    },
  });
}
```

### SSE 订阅模式

```tsx
useEffect(() => {
  const es = new EventSource(`/api/accounts/connect/${accountId}/stream`);
  es.addEventListener("status", (e) => {
    const status = JSON.parse(e.data);
    setConnectionStatus(status);
    if (status.stage === "done" || status.stage === "error") {
      es.close();
    }
  });
  return () => es.close();
}, [accountId]);
```

### Ant Design 表格 + 分页模式

```tsx
const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });

const { data, isLoading } = useQuery({
  queryKey: ["xxx", pagination],
  queryFn: () =>
    api.getXxxList({
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize,
    }),
});

<Table
  dataSource={data?.items}
  loading={isLoading}
  pagination={{
    current: pagination.current,
    pageSize: pagination.pageSize,
    total: data?.total,
    onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
  }}
/>
```

---

## 会话恢复点格式

```markdown
### 会话恢复点
- 最后完成: {文件/功能}
- 当前进度: {已完成数}/{总数}
- 下一个: {下一个任务}
- 待注意: {重要提示}
```

---

## 质量门禁

```bash
# 后端 (Python)
cd backend && python -m mypy .          # 类型检查
cd backend && python -m pytest          # 单元测试

# 前端 (TypeScript)
cd frontend && npm run typecheck        # tsc --noEmit
cd frontend && npm run lint             # ESLint
```
