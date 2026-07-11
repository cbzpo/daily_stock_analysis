# Launch WebUI

启动 daily_stock_analysis 的 WebUI 服务，自动处理端口冲突和进程管理。

## Usage

```text
/launch-webui [--port PORT] [--host HOST]
```

默认端口: 9000，默认绑定: 127.0.0.1。

## Instructions

### Step 1: 检查前端构建产物

```bash
ls apps/dsa-web/dist
```

如果 `dist/` 目录不存在或为空，先构建前端：

```bash
cd apps/dsa-web && npm ci && npm run build
```

### Step 2: 端口可用性检查

```bash
netstat -an | Select-String ":<port>"
```

如果端口已被占用：

1. 尝试查找占用进程：`Get-Process -Name python | Select-Object Id,ProcessName,StartTime`
2. 如果是之前的 WebUI 实例，询问用户是否终止
3. 如果用户确认，终止旧进程：`taskkill /F /PID <pid>`
4. 如果端口仍被其他进程占用，自动递增端口（9000 → 9001 → 9002…）直到找到可用端口

### Step 3: 启动服务

后台启动 WebUI：

```powershell
Start-Process python -ArgumentList "main.py","--webui-only","--port","<port>","--host","<host>" -WorkingDirectory "<project_dir>" -WindowStyle Hidden
```

如需外部访问（非本机），使用 `--host 0.0.0.0`。

### Step 4: 验证启动

等待 5-10 秒后检查端口绑定：

```powershell
Start-Sleep -Seconds 10; netstat -an | Select-String ":<port>"
```

同时检查 Python 进程是否存活：

```powershell
Get-Process python | Select-Object Id,ProcessName,StartTime
```

### Step 5: 输出访问地址

```
WebUI 已启动: http://<host>:<port>
API 文档: http://<host>:<port>/docs
```

## Allowed Auto-Actions (No Confirmation Needed)

- 检查端口占用状态
- 构建前端（如缺失）
- 启动 WebUI 后台进程
- 检查进程和端口状态

## Actions Requiring Confirmation

1. 终止占用目标端口的现有 Python 进程
2. 使用 `--host 0.0.0.0` 允许外部访问（安全提醒）
