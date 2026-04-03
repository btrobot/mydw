# DewuGoJin CLI 使用指南

## 快速开始

```bash
# 进入 CLI 目录
cd frontend/scripts/cli

# 安装依赖
npm install

# 运行健康检查
npm run dev -- health
```

## 命令详解

### health

检查后端服务健康状态。

```bash
dewu-cli health
```

### account

账号管理操作。

```bash
# 查看账号列表
dewu-cli account list

# 查看账号详情
dewu-cli account <id>
```

### test

测试指定 API 域。

```bash
dewu-cli test accounts
dewu-cli test auth
dewu-cli test health
```

### get

发送 GET 请求。

```bash
dewu-cli get /api/accounts
dewu-cli get /api/accounts/1
```

### post

发送 POST 请求。

```bash
dewu-cli post /api/accounts '{"username": "test"}'
```

## 环境配置

```bash
export BASE_URL=http://localhost:8000
```
