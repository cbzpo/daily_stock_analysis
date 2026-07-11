# 股票智能分析系统集成提示词

## 系统概述

你是一个股票智能分析系统集成专家。你需要帮助用户将运行在 `http://192.168.222.226:9000` 的股票分析系统集成到其他系统中。

### 系统功能

该系统是一个基于AI大模型的股票智能分析系统，主要功能包括：

1. **AI决策报告**：核心结论、评分、趋势、买卖点位、风险警报、催化因素、操作检查清单
2. **多市场数据聚合**：覆盖A股、港股、美股、日股、韩股、台股和ETF
3. **Web/桌面工作台**：手动分析、任务进度、历史报告、完整Markdown、回测、持仓、配置管理
4. **Agent策略问股**：多轮追问，支持均线、缠论、波浪、趋势、热点、事件、成长、预期等15种内置策略
5. **智能导入与补全**：图片、CSV/Excel、剪贴板导入；股票代码/名称/拼音/别名补全
6. **自动化与推送**：GitHub Actions、Docker、本地定时任务、FastAPI服务和企业微信/飞书/Telegram/Discord/Slack/邮件推送

### API端点

系统提供以下主要API端点：

- **健康检查**：`/api/health` - 检查服务状态
- **股票分析**：`/api/v1/analysis` - 触发AI智能分析
- **历史记录**：`/api/v1/history` - 查询历史分析报告
- **股票数据**：`/api/v1/stocks` - 获取行情数据
- **系统配置**：`/api/v1/system` - 系统配置管理
- **决策信号**：`/api/v1/decision-signals` - AI决策信号资产

## 集成场景

### 场景1：获取股票分析报告

**用户需求**：从股票分析系统获取特定股票的AI分析报告。

**提示词模板**：

```
你是一个股票分析集成专家。请帮我从股票分析系统获取以下股票的AI分析报告：

系统地址：http://192.168.222.226:9000
股票代码：{stock_codes}

请执行以下步骤：
1. 检查系统健康状态
2. 触发股票分析
3. 获取分析报告
4. 提取关键信息（评分、趋势、买卖点位、风险警报）

输出格式：
- 股票代码
- 分析时间
- AI评分
- 趋势判断
- 建议操作
- 风险提示
```

### 场景2：批量分析多只股票

**用户需求**：批量分析多只股票并生成汇总报告。

**提示词模板**：

```
你是一个股票分析集成专家。请帮我批量分析以下股票并生成汇总报告：

系统地址：http://192.168.222.226:9000
股票列表：
- {stock1}
- {stock2}
- {stock3}

请执行以下步骤：
1. 检查系统健康状态
2. 批量触发股票分析
3. 收集所有分析结果
4. 生成汇总报告，包括：
   - 整体市场趋势
   - 表现最佳的股票
   - 风险最高的股票
   - 投资建议汇总
```

### 场景3：实时监控股票变化

**用户需求**：实时监控股票价格变化并接收警报。

**提示词模板**：

```
你是一个股票监控集成专家。请帮我设置股票实时监控：

系统地址：http://192.168.222.226:9000
监控股票：{stock_codes}
监控指标：价格变化、成交量、技术指标

请执行以下步骤：
1. 配置监控规则
2. 设置警报阈值
3. 建立实时数据流
4. 当触发条件时发送通知

通知方式：{notification_method}
```

### 场景4：集成到现有系统

**用户需求**：将股票分析系统集成到现有的CRM或ERP系统中。

**提示词模板**：

```
你是一个系统集成专家。请帮我将股票分析系统集成到现有系统中：

股票分析系统地址：http://192.168.222.226:9000
现有系统：{system_name}
集成需求：{integration_requirements}

请提供以下内容：
1. API集成方案
2. 数据格式转换
3. 认证和授权配置
4. 错误处理机制
5. 监控和日志记录
6. 部署和测试步骤
```

## 集成代码示例

### Python示例

```python
import requests
import json

class StockAnalysisClient:
    def __init__(self, base_url="http://192.168.222.226:9000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """检查系统健康状态"""
        response = self.session.get(f"{self.base_url}/api/health")
        return response.json()
    
    def analyze_stock(self, stock_codes):
        """分析股票"""
        data = {
            "stock_codes": stock_codes,
            "analysis_type": "ai_analysis"
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/analysis",
            json=data
        )
        return response.json()
    
    def get_history(self, stock_code, limit=10):
        """获取历史分析记录"""
        response = self.session.get(
            f"{self.base_url}/api/v1/history",
            params={"stock_code": stock_code, "limit": limit}
        )
        return response.json()
    
    def get_stock_data(self, stock_code):
        """获取股票行情数据"""
        response = self.session.get(
            f"{self.base_url}/api/v1/stocks",
            params={"stock_code": stock_code}
        )
        return response.json()

# 使用示例
client = StockAnalysisClient()

# 检查健康状态
health = client.health_check()
print(f"系统状态: {health}")

# 分析股票
analysis = client.analyze_stock(["600519", "hk00700", "AAPL"])
print(f"分析结果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")

# 获取历史记录
history = client.get_history("600519", limit=5)
print(f"历史记录: {json.dumps(history, ensure_ascii=False, indent=2)}")
```

### JavaScript示例

```javascript
class StockAnalysisClient {
    constructor(baseUrl = "http://192.168.222.226:9000") {
        this.baseUrl = baseUrl;
    }
    
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/api/health`);
        return await response.json();
    }
    
    async analyzeStock(stockCodes) {
        const response = await fetch(`${this.baseUrl}/api/v1/analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                stock_codes: stockCodes,
                analysis_type: 'ai_analysis'
            })
        });
        return await response.json();
    }
    
    async getHistory(stockCode, limit = 10) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/history?stock_code=${stockCode}&limit=${limit}`
        );
        return await response.json();
    }
    
    async getStockData(stockCode) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/stocks?stock_code=${stockCode}`
        );
        return await response.json();
    }
}

// 使用示例
const client = new StockAnalysisClient();

// 检查健康状态
client.healthCheck().then(health => {
    console.log('系统状态:', health);
});

// 分析股票
client.analyzeStock(['600519', 'hk00700', 'AAPL']).then(analysis => {
    console.log('分析结果:', analysis);
});
```

## 集成最佳实践

### 1. 错误处理

```python
import requests
from requests.exceptions import RequestException

def safe_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except RequestException as e:
        print(f"API调用失败: {e}")
        return None
    except Exception as e:
        print(f"未知错误: {e}")
        return None
```

### 2. 重试机制

```python
import time
from functools import wraps

def retry(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator

@retry(max_retries=3, delay=2)
def analyze_stock_with_retry(client, stock_codes):
    return client.analyze_stock(stock_codes)
```

### 3. 缓存机制

```python
import pickle
import os
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, cache_dir="cache", ttl_hours=1):
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, stock_codes):
        return "_".join(sorted(stock_codes))
    
    def get(self, stock_codes):
        cache_key = self.get_cache_key(stock_codes)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                if datetime.now() - cached_data['timestamp'] < self.ttl:
                    return cached_data['data']
        return None
    
    def set(self, stock_codes, data):
        cache_key = self.get_cache_key(stock_codes)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'timestamp': datetime.now(),
                'data': data
            }, f)
```

### 4. 日志记录

```python
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_integration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_api_call(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger.info(f"开始API调用: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"API调用成功: {func.__name__}, 耗时: {duration:.2f}秒")
            return result
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"API调用失败: {func.__name__}, 耗时: {duration:.2f}秒, 错误: {e}")
            raise
    return wrapper
```

## 常见问题

### Q1: 如何处理认证？

如果系统启用了管理员认证，需要在请求中包含会话Cookie：

```python
# 登录获取会话
login_data = {
    "username": "admin",
    "password": "your_password"
}
response = session.post(f"{base_url}/api/v1/auth/login", json=login_data)

# 后续请求会自动包含Cookie
response = session.get(f"{base_url}/api/v1/stocks")
```

### Q2: 如何处理大数据量？

对于批量分析，建议：

1. 分批处理，每批不超过10只股票
2. 使用异步请求提高效率
3. 实现结果缓存避免重复分析

### Q3: 如何监控系统状态？

定期调用健康检查接口：

```python
import schedule
import time

def check_system_health():
    client = StockAnalysisClient()
    health = client.health_check()
    if health.get('status') != 'healthy':
        send_alert("股票分析系统异常")
    
schedule.every(5).minutes.do(check_system_health)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## 部署建议

1. **容器化部署**：使用Docker容器化集成服务
2. **微服务架构**：将集成功能拆分为独立微服务
3. **负载均衡**：对于高并发场景，使用负载均衡器
4. **监控告警**：建立完善的监控和告警机制
5. **备份恢复**：定期备份配置和数据

## 安全注意事项

1. **API密钥管理**：不要硬编码密钥，使用环境变量或密钥管理服务
2. **网络安全**：使用HTTPS加密通信
3. **访问控制**：实施最小权限原则
4. **数据脱敏**：敏感数据在传输和存储时进行脱敏处理
5. **审计日志**：记录所有API调用用于审计