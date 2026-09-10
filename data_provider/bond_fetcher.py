# -*- coding: utf-8 -*-
"""
===================================
BondFetcher - 可转债数据源
===================================

支持可转债历史数据获取
使用 AkShare 库获取可转债历史K线数据

可转债代码格式：
- 113050 (南银转债)
- 127060 (本钢转债)
- 128135 (泰林转债)
"""

import logging
import time
from typing import Optional, List, Dict, Any

import pandas as pd

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS, normalize_stock_code

logger = logging.getLogger(__name__)


def is_convertible_bond(code: str) -> bool:
    """判断是否为可转债代码"""
    code = code.strip()
    # 可转债代码通常以 113、127、128、118、123 开头，共6位数字
    if code.isdigit() and len(code) == 6:
        if code.startswith(('113', '127', '128', '118', '123')):
            return True
    return False


def normalize_bond_code(code: str) -> str:
    """规范化可转债代码"""
    code = code.strip()
    # 去除可能的前缀
    if code.startswith('SH') or code.startswith('SZ'):
        code = code[2:]
    # 补齐6位
    if code.isdigit() and len(code) < 6:
        code = code.zfill(6)
    return code


def get_bond_symbol(code: str) -> str:
    """获取可转债的AkShare符号格式"""
    code = normalize_bond_code(code)
    # 可转债代码以113、128开头的在上海交易所
    if code.startswith(('113', '128')):
        return f"sh{code}"
    else:
        return f"sz{code}"


class BondFetcher(BaseFetcher):
    """可转债数据源 - 使用 AkShare"""
    
    name = "BondFetcher"
    priority = 6  # 优先级低于股票数据源
    
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取可转债历史数据
        
        Args:
            stock_code: 可转债代码，如 113050
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            
        Returns:
            原始数据 DataFrame
        """
        code = normalize_bond_code(stock_code)
        symbol = get_bond_symbol(code)
        
        try:
            import akshare as ak
            
            # 使用 AkShare 获取可转债历史K线数据
            logger.info(f"[BondFetcher] 获取可转债 {code} 历史数据...")
            df = ak.bond_zh_hs_cov_daily(symbol=symbol)
            
            if df is not None and not df.empty:
                # 标准化数据
                df = self._normalize_data(df, stock_code)
                
                logger.info(f"[BondFetcher] 获取到 {len(df)} 条可转债 {code} 数据")
                return df
            else:
                raise DataFetchError(f"未获取到可转债 {code} 的数据")
                
        except Exception as e:
            logger.error(f"[BondFetcher] 获取可转债数据失败: {e}")
            raise DataFetchError(f"可转债 {code} 数据获取失败: {str(e)}")
    
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
        
        # 计算涨跌幅
        if 'close' in result.columns and len(result) > 1:
            result['pct_chg'] = result['close'].pct_change() * 100
        
        # 填充缺失列
        for col in STANDARD_COLUMNS:
            if col not in result.columns:
                result[col] = 0
        
        return result
