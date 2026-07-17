# -*- coding: utf-8 -*-
"""
SinaFetcher 单元测试

测试新浪财经数据源的基本功能。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_provider.sina_fetcher import SinaFetcher, _to_sina_symbol


def test_to_sina_symbol():
    """测试股票代码转换。"""
    # A股
    assert _to_sina_symbol("600519") == "sh600519"
    assert _to_sina_symbol("000001") == "sz000001"
    assert _to_sina_symbol("300750") == "sz300750"

    # 带前缀
    assert _to_sina_symbol("SH600519") == "sh600519"
    assert _to_sina_symbol("sz000001") == "sz000001"

    # 港股
    assert _to_sina_symbol("HK00700") == "hk00700"
    assert _to_sina_symbol("hk01810") == "hk01810"

    # 美股
    assert _to_sina_symbol("AAPL") == "gb_aapl"
    assert _to_sina_symbol("TSLA") == "gb_tsla"

    print("✅ _to_sina_symbol 测试通过")


def test_fetcher_initialization():
    """测试数据源初始化。"""
    fetcher = SinaFetcher()
    assert fetcher.name == "SinaFetcher"
    assert fetcher.priority == 5
    assert fetcher.allow_empty_daily_data is True
    print("✅ SinaFetcher 初始化测试通过")


def test_fetch_daily_data():
    """测试获取日线数据（需要网络）。"""
    fetcher = SinaFetcher()

    try:
        # 测试A股
        df = fetcher.get_daily_data("600519", days=10)
        if not df.empty:
            print(f"✅ A股(600519) 日线数据获取成功: {len(df)} 行")
            print(f"   日期范围: {df['date'].min()} ~ {df['date'].max()}")
        else:
            print("⚠️ A股(600519) 返回空数据（可能非交易时段）")
    except Exception as e:
        print(f"⚠️ A股(600519) 获取失败: {e}")

    # 注意：当前新浪API端点仅支持A股，港股/美股需要其他端点
    print("ℹ️ 新浪财经K线API当前仅支持A股，港股/美股暂不支持")


if __name__ == "__main__":
    print("=" * 50)
    print("SinaFetcher 单元测试")
    print("=" * 50)

    test_to_sina_symbol()
    test_fetcher_initialization()

    print("\n" + "=" * 50)
    print("网络测试（可能需要几秒）")
    print("=" * 50)
    test_fetch_daily_data()

    print("\n✅ 所有测试完成")
