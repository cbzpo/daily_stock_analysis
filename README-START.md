# 一键启动说明

## 快速开始

### 方式一：双击启动（推荐新手）

1. 双击 `start.bat`
2. 选择启动模式（输入 1-4）
3. 等待启动完成

### 方式二：PowerShell 启动（推荐进阶用户）

```powershell
# 交互式启动
.\start.ps1

# 后台启动 WebUI
.\start.ps1 -Background

# 指定端口
.\start.ps1 -Port 9001

# 停止服务
.\start.ps1 -Stop

# 查看状态
.\start.ps1 -Status

# 查看日志
.\start.ps1 -Log
```

## 启动模式说明

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| WebUI 看板 | 启动 Web 管理界面 | 日常使用，浏览器管理 |
| 单次分析 | 执行一次股票分析 | 临时查看分析结果 |
| 定时任务 | 每日自动执行分析 | 长期自动运行 |
| 调试模式 | 详细日志输出 | 排查问题 |

## 常见问题

### Q: 端口被占用怎么办？

脚本会自动检测端口占用并询问是否停止占用进程。如果选择不停止，会自动切换到下一个可用端口。

### Q: 如何修改自选股？

编辑 `.env` 文件，修改 `STOCK_LIST` 配置：

```
STOCK_LIST=600519,300750,601899
```

### Q: 如何配置通知渠道？

编辑 `.env` 文件，配置对应的通知渠道，例如：

```
# 企业微信
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 飞书
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# 邮件
EMAIL_SENDER=your@email.com
EMAIL_PASSWORD=your_password
```

### Q: 如何查看日志？

```powershell
# PowerShell 方式
.\start.ps1 -Log

# 或直接查看日志目录
notepad logs\stock_analysis_YYYYMMDD.log
```

### Q: 如何停止服务？

```powershell
# PowerShell 方式
.\start.ps1 -Stop

# 或双击 stop.bat
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `start.bat` | Windows 双击即用启动脚本 |
| `start.ps1` | PowerShell 增强启动脚本 |
| `stop.bat` | 停止服务脚本 |
| `.env` | 环境变量配置文件 |
| `main.py` | 主程序入口 |
| `logs/` | 日志目录 |
| `data/` | 数据库目录 |
| `reports/` | 分析报告目录 |
