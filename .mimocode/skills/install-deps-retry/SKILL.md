# Install Deps Retry

自动检测 Python 项目缺失依赖并逐个安装，避免反复手动排查 ImportError。

## Usage

```text
/install-deps-retry <command> [working_dir]
```

`<command>` 是要运行的目标命令（如 `python main.py --dry-run`）。
`[working_dir]` 可选，默认为当前目录。

## Instructions

### Step 1: 首次尝试

在目标目录执行用户指定的命令，捕获输出：

```bash
python <command> 2>&1
```

### Step 2: 识别缺失依赖

从输出中提取 `ModuleNotFoundError` 或 `ImportError` 行，解析出缺失的模块名。

常见映射表（模块名 → pip 包名）：

| 模块名 | pip 包名 |
|--------|----------|
| `dotenv` | `python-dotenv` |
| `tenacity` | `tenacity` |
| `sqlalchemy` | `sqlalchemy` |
| `schedule` | `schedule` |
| `exchange_calendars` | `exchange-calendars` |
| `efinance` | `efinance` |
| `akshare` | `akshare` |
| `tushare` | `tushare` |
| `pytdx` | `pytdx` |
| `baostock` | `baostock` |
| `pypinyin` | `pypinyin` |
| `json_repair` | `json-repair` |
| `tavily` | `tavily-python` |
| `google_search` | `google-search-results` |
| `litellm` | `litellm` |
| `fake_useragent` | `fake-useragent` |
| `markdown2` | `markdown2` |
| `newspaper` | `newspaper3k` |
| `lxml_html_clean` | `lxml_html_clean` |
| `feedparser` | `feedparser` |
| `requests` | `requests` |
| `aiohttp` | `aiohttp` |
| `numpy` | `numpy` |
| `pandas` | `pandas` |
| `greenlet` | `greenlet` |

若模块名不在映射表中，尝试 `pip install <模块名>`（下划线转连字符）。

### Step 3: 逐个安装

对每个缺失模块执行：

```bash
pip install <pip_package_name>
```

单个包安装超时设为 120 秒。安装失败时记录错误并跳过，继续下一个。

### Step 4: 重试验证

全部安装完成后，重新执行用户指定的命令。如果仍然失败：

- 再次提取新的 `ModuleNotFoundError`
- 重复 Step 2-3（最多 3 轮）
- 超过 3 轮仍有缺失，停止并输出剩余缺失列表

### Step 5: 报告结果

输出格式：

```
✅ 已安装: <包列表>
❌ 失败: <包列表> (原因)
⏭️ 跳过: <包列表> (原因)

最终命令执行结果: [成功/失败]
```

## Allowed Auto-Actions (No Confirmation Needed)

- 执行 `pip install` 安装缺失依赖
- 执行用户指定的验证命令
- 读取命令输出以提取错误信息

## Actions Requiring Confirmation

无 — 所有操作均为本地非破坏性操作。
