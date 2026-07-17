# -*- coding: utf-8 -*-
"""
===================================
SinaFetcher - 新浪财经数据源 (Priority -1)
===================================

数据来源：新浪财经历史K线接口
特点：免费、无需Token、数据较全面
风险：接口偶尔不稳定

支持市场：A股
"""

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS, normalize_stock_code, is_bse_code

logger = logging.getLogger(__name__)

# 新浪财经历史K线接口（可用端点）
_SINA_KLINE_ENDPOINT = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
_SINA_REALTIME_ENDPOINT = "https://hq.sinajs.cn/list"
_HTTP_TIMEOUT_SECONDS = 10

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _to_sina_symbol(stock_code: str) -> str:
    """将标准化股票代码转换为新浪格式（sh600519/sz000001/hk00700）。"""
    code = normalize_stock_code(stock_code)
    if not code:
        return ""

    upper = code.upper()

    # 港股
    if upper.startswith("HK"):
        digits = upper[2:]
        if digits.isdigit():
            return f"hk{digits.zfill(5)}"
        return ""

    # 美股（新浪美股格式：gb_aapl）
    if code.isalpha() and code.isascii():
        return f"gb_{code.lower()}"

    # A股/ETF
    if code.isdigit() and len(code) <= 6:
        padded = code.zfill(6)
        if is_bse_code(padded):
            return f"bj{padded}"
        if padded.startswith(("6", "5", "9")):
            return f"sh{padded}"
        return f"sz{padded}"

    return ""


def _empty_daily_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=STANDARD_COLUMNS)


class SinaFetcher(BaseFetcher):
    """新浪财经历史K线数据源（A股/港股/美股）。"""

    name = "SinaFetcher"
    priority = -1  # 最高优先级（比其他0优先级更优先）
    allow_empty_daily_data = True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError)),
        before_sleep=lambda retry_state: logger.debug(
            "SinaFetcher retry %d for %s",
            retry_state.attempt_number,
            getattr(retry_state, "_stock_code", "unknown"),
        ),
    )
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从新浪财经获取历史K线数据。

        使用 JSONP 接口获取日线数据，自动处理日期范围和分页。
        """
        symbol = _to_sina_symbol(stock_code)
        if not symbol:
            raise DataFetchError(f"SinaFetcher: 无法转换股票代码 {stock_code}")

        # 计算需要获取的天数（多取一些以确保覆盖）
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days = max(30, (end_dt - start_dt).days + 60)
        except ValueError:
            days = 120

        # 构建请求参数
        # 新浪K线接口格式：symbol, scale(240=日线), ma, datalen
        params = {
            "symbol": symbol,
            "scale": "240",  # 240分钟 = 日线
            "ma": "no",
            "datalen": min(days, 800),  # 新浪最大支持约800条
        }

        headers = {
            "User-Agent": random.choice(_USER_AGENTS),
            "Referer": "https://finance.sina.com.cn",
        }

        try:
            response = requests.get(
                _SINA_KLINE_ENDPOINT,
                params=params,
                headers=headers,
                timeout=_HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise DataFetchError(f"SinaFetcher: 请求失败 {stock_code}: {e}") from e

        # 解析响应（新浪返回的是JSONP格式，需要提取JSON部分）
        text = response.text.strip()
        # 提取JSON数组部分：var _xxx = [...]
        json_start = text.find("[")
        json_end = text.rfind("]")
        if json_start == -1 or json_end == -1:
            logger.info("SinaFetcher: 无法解析响应 for %s", stock_code)
            return _empty_daily_frame()

        import json
        try:
            data = json.loads(text[json_start:json_end + 1])
        except json.JSONDecodeError as e:
            raise DataFetchError(f"SinaFetcher: JSON解析失败 {stock_code}: {e}") from e

        if not data:
            return _empty_daily_frame()

        # 转换为DataFrame
        rows = []
        for item in data:
            try:
                rows.append({
                    "date": item.get("day", ""),
                    "open": float(item.get("open", 0)),
                    "high": float(item.get("high", 0)),
                    "low": float(item.get("low", 0)),
                    "close": float(item.get("close", 0)),
                    "volume": float(item.get("volume", 0)),
                    "amount": 0.0,  # 新浪K线接口不提供成交额
                })
            except (ValueError, TypeError):
                continue

        if not rows:
            return _empty_daily_frame()

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        # 过滤日期范围
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        return df

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化列名为项目统一格式。"""
        normalized = df.copy()

        # 确保数值类型
        for col in ("open", "high", "low", "close", "volume", "amount"):
            if col in normalized.columns:
                normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

        # 计算涨跌幅（如果没有）
        if "pct_chg" not in normalized.columns:
            normalized["pct_chg"] = normalized["close"].pct_change().fillna(0.0) * 100

        # 选择标准列
        normalized = normalized[STANDARD_COLUMNS]
        return normalized

    def get_realtime_quote(self, stock_code: str) -> Optional[dict]:
        """
        获取实时行情（可选实现）。

        返回格式与项目 UnifiedRealtimeQuote 兼容。
        """
        symbol = _to_sina_symbol(stock_code)
        if not symbol:
            return None

        headers = {
            "User-Agent": random.choice(_USER_AGENTS),
            "Referer": "https://finance.sina.com.cn",
        }

        try:
            response = requests.get(
                f"{_SINA_REALTIME_ENDPOINT}/{symbol}",
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
        except requests.RequestException:
            return None

        # 解析新浪实时行情格式：var hq_str_sh600519="名称,开盘价,昨收,当前价,..."
        text = response.text.strip()
        data_start = text.find('"')
        data_end = text.rfind('"')
        if data_start == -1 or data_end == -1 or data_start == data_end:
            return None

        fields = text[data_start + 1:data_end].split(",")
        if len(fields) < 32:
            return None

        try:
            return {
                "name": fields[0],
                "current_price": float(fields[3]),
                "change": float(fields[3]) - float(fields[2]),
                "change_pct": ((float(fields[3]) - float(fields[2])) / float(fields[2]) * 100) if float(fields[2]) > 0 else 0,
                "open": float(fields[1]),
                "high": float(fields[4]),
                "low": float(fields[5]),
                "volume": float(fields[8]),
                "amount": float(fields[9]),
                "pe_ratio": float(fields[39]) if len(fields) > 39 and fields[39] else None,
                "source": "sina",
            }
        except (ValueError, IndexError):
            return None
