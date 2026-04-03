# DewuGoJin CLI

得物掘金工具 API 测试 CLI

## 安装

```bash
cd frontend/scripts/cli
npm install
```

## 使用方法

### 开发模式

```bash
npm run dev -- <command>
```

### 直接运行

```bash
npx tsx src/index.ts <command>
```

## 命令

### 账号管理 (account)

```bash
dewu-cli account list              # 列出得物账号
dewu-cli account add <id> <name>   # 添加账号
dewu-cli account remove <id>       # 删除账号
dewu-cli account status <id>       # 查看账号状态
dewu-cli account stats             # 查看统计信息
```

### 连接管理

```bash
dewu-cli connect <id> [--phone <phone>]  # 建立连接
dewu-cli disconnect <id>                 # 断开连接
dewu-cli status <id>                     # 查看连接状态
```

### HTTP 请求

```bash
dewu-cli get <path>                 # GET 请求
dewu-cli post <path> [json]         # POST 请求
dewu-cli put <path> [json]          # PUT 请求
dewu-cli delete <path>              # DELETE 请求
```

### 测试套件

```bash
dewu-cli test accounts    # 测试账号 API
dewu-cli test tasks       # 测试任务 API
dewu-cli test materials   # 测试素材 API
dewu-cli test all         # 测试所有 API
```

### 系统

```bash
dewu-cli health           # 后端健康检查
dewu-cli --help            # 显示帮助
dewu-cli --version         # 显示版本
```

## 环境变量

- `BASE_URL` - API 基础地址 (默认: http://localhost:8000)

## 示例

```bash
# 健康检查
dewu-cli health

# 账号管理
dewu-cli account list
dewu-cli account add test001 测试账号
dewu-cli account status 1

# 连接管理
dewu-cli connect 1 --phone 13800138000
dewu-cli disconnect 1

# HTTP 请求
dewu-cli get /api/accounts
dewu-cli post /api/accounts '{"account_id": "test", "account_name": "测试"}'

# 运行测试
dewu-cli test all
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| /api/accounts | GET | 账号列表 |
| /api/accounts | POST | 创建账号 |
| /api/accounts/{id} | GET | 账号详情 |
| /api/accounts/{id} | DELETE | 删除账号 |
| /api/accounts/stats | GET | 账号统计 |
| /api/accounts/connect/{id} | POST | 建立连接 |
| /api/accounts/disconnect/{id} | POST | 断开连接 |
| /api/tasks | GET | 任务列表 |
| /api/tasks/stats | GET | 任务统计 |
| /api/materials | GET | 素材列表 |
| /api/materials/stats | GET | 素材统计 |
