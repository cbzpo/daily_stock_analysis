# -*- coding: utf-8 -*-
"""
===================================
FundFetcher - 基金/ETF 数据源
===================================

支持基金和ETF历史数据获取
使用 AkShare 库获取基金/ETF 历史K线数据

基金代码格式：
- 510300 (沪深300ETF)
- 159915 (创业板ETF)
- 110011 (易方达中小盘混合)
"""

import logging
import time
from typing import Optional, List, Dict, Any

import pandas as pd

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS, normalize_stock_code

logger = logging.getLogger(__name__)


def is_etf(code: str) -> bool:
    """判断是否为ETF代码"""
    code = code.strip()
    # ETF 代码通常是 51xxxx, 15xxxx, 16xxxx 等
    if code.isdigit() and len(code) == 6:
        if code.startswith(('51', '15', '16', '50', '56', '58')):
            return True
    return False


def is_fund(code: str) -> bool:
    """判断是否为基金代码"""
    code = code.strip()
    # 基金代码通常是 6位数字（开放式基金）
    if code.isdigit() and len(code) == 6:
        if code.startswith(('00', '11', '16', '51', '15')):
            return True
    return False


def normalize_fund_code(code: str) -> str:
    """规范化基金代码"""
    code = code.strip()
    # 去除可能的前缀
    if code.startswith('sh') or code.startswith('sz') or code.startswith('SH') or code.startswith('SZ'):
        code = code[2:]
    # 补齐6位
    if code.isdigit() and len(code) < 6:
        code = code.zfill(6)
    return code


def get_fund_symbol(code: str) -> str:
    """获取基金的AkShare符号格式"""
    code = normalize_fund_code(code)
    # 根据代码前缀判断交易所
    if code.startswith(('51', '50', '56', '58')):
        return f"sh{code}"
    elif code.startswith(('15', '16')):
        return f"sz{code}"
    else:
        # 默认尝试上海交易所
        return f"sh{code}"


class FundFetcher(BaseFetcher):
    """基金/ETF 数据源 - 使用 AkShare"""
    
    name = "FundFetcher"
    priority = 7  # 优先级低于股票和可转债数据源
    
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取基金/ETF 历史数据
        
        Args:
            stock_code: 基金代码，如 510300
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            
        Returns:
            原始数据 DataFrame
        """
        code = normalize_fund_code(stock_code)
        symbol = get_fund_symbol(code)
        
        try:
            import akshare as ak
            
            # 使用 AkShare 获取 ETF 历史数据
            logger.info(f"[FundFetcher] 获取基金 {code} 历史数据...")
            
            # 尝试 fund_etf_hist_sina
            df = ak.fund_etf_hist_sina(symbol=symbol)
            
            if df is not None and not df.empty:
                # 标准化数据
                df = self._normalize_data(df, stock_code)
                
                logger.info(f"[FundFetcher] 获取到 {len(df)} 条基金 {code} 数据")
                return df
            else:
                raise DataFetchError(f"未获取到基金 {code} 的数据")
                
        except Exception as e:
            logger.error(f"[FundFetcher] 获取基金数据失败: {e}")
            raise DataFetchError(f"基金 {code} 数据获取失败: {str(e)}")
    
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化数据列名"""
        result = pd.DataFrame(columns=STANDARD_COLUMNS)
        
        # 映射列名
        if 'date' in df.columns:
            result['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        if 'open' in df.columns:
            result['open'] = pd.to_numeric(df['open'], errors='coerce')
        if 'close' in df.columns:
            result['close'] = pd.to_numeric(df['close'], errors='coerce')
        if 'high' in df.columns:
            result['high'] = pd.to_numeric(df['high'], errors='coerce')
        if 'low' in df.columns:
            result['low'] = pd.to_numeric(df['low'], errors='coerce')
        if 'volume' in df.columns:
            result['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        if 'amount' in df.columns:
            result['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # 计算涨跌幅
        if 'close' in result.columns and len(result) > 1:
            result['pct_chg'] = result['close'].pct_change() * 100
        
        # 填充缺失列
        for col in STANDARD_COLUMNS:
            if col not in result.columns:
                result[col] = 0
        
        return result
