# -*- coding: utf-8 -*-
"""
SinaFetcher 端到端测试

测试新数据源在日常分析流程中的表现。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta


def test_data_fetcher_manager_integration():
    """测试与 DataFetcherManager 的集成。"""
    print("=" * 60)
    print("测试1: DataFetcherManager 集成")
    print("=" * 60)

    try:
        from data_provider import DataFetcherManager, SinaFetcher

        # 初始化管理器
        manager = DataFetcherManager()

        # 检查 SinaFetcher 是否在数据源列表中
        fetchers = manager._get_fetchers_snapshot()
        sina_fetcher = None
        for f in fetchers:
            if f.name == "SinaFetcher":
                sina_fetcher = f
                break

        if sina_fetcher:
            print(f"✅ SinaFetcher 已注册，优先级: {sina_fetcher.priority}")
        else:
            print("❌ SinaFetcher 未找到")
            return False

        # 测试获取日线数据
        print("\n获取 600519（贵州茅台）日线数据...")
        df, source = manager.get_daily_data("600519", days=30)

        if not df.empty:
            print(f"✅ 数据获取成功")
            print(f"   数据来源: {source}")
            print(f"   数据行数: {len(df)}")
            print(f"   日期范围: {df['date'].min()} ~ {df['date'].max()}")
            print(f"   最新收盘价: {df['close'].iloc[-1]:.2f}")
            return True
        else:
            print("⚠️ 返回空数据")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_technical_indicators():
    """测试技术指标计算。"""
    print("\n" + "=" * 60)
    print("测试2: 技术指标计算")
    print("=" * 60)

    try:
        from data_provider import DataFetcherManager

        manager = DataFetcherManager()
        df, source = manager.get_daily_data("600519", days=60)

        if df.empty:
            print("⚠️ 无法获取数据，跳过测试")
            return False

        # 检查技术指标是否已计算
        expected_cols = ["ma5", "ma10", "ma20", "volume_ratio"]
        missing_cols = [col for col in expected_cols if col not in df.columns]

        if missing_cols:
            print(f"❌ 缺少技术指标列: {missing_cols}")
            return False

        print("✅ 技术指标已计算")
        print(f"   MA5: {df['ma5'].iloc[-1]:.2f}")
        print(f"   MA10: {df['ma10'].iloc[-1]:.2f}")
        print(f"   MA20: {df['ma20'].iloc[-1]:.2f}")
        print(f"   量比: {df['volume_ratio'].iloc[-1]:.2f}")

        # 检查趋势判断
        ma5 = df['ma5'].iloc[-1]
        ma10 = df['ma10'].iloc[-1]
        ma20 = df['ma20'].iloc[-1]

        if ma5 > ma10 > ma20:
            print("   趋势: 多头排列 ✅")
        elif ma5 < ma10 < ma20:
            print("   趋势: 空头排列")
        else:
            print("   趋势: 盘整")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_analyzer_integration():
    """测试与 StockTrendAnalyzer 的集成。"""
    print("\n" + "=" * 60)
    print("测试3: StockTrendAnalyzer 集成")
    print("=" * 60)

    try:
        from src.stock_analyzer import StockTrendAnalyzer, analyze_stock
        from data_provider import DataFetcherManager

        # 获取数据
        manager = DataFetcherManager()
        df, source = manager.get_daily_data("600519", days=60)

        if df.empty:
            print("⚠️ 无法获取数据，跳过测试")
            return False

        # 执行分析
        result = analyze_stock(df, code="600519")

        if result:
            print("✅ StockTrendAnalyzer 分析完成")
            print(f"   趋势状态: {result.trend_status.value}")
            print(f"   趋势强度: {result.trend_strength:.1f}%")
            print(f"   乖离率(MA5): {result.bias_ma5:.2f}%")
            print(f"   买入信号: {result.buy_signal.value}")
            return True
        else:
            print("⚠️ 分析器返回空结果")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_stock_batch():
    """测试批量获取多只股票数据。"""
    print("\n" + "=" * 60)
    print("测试4: 批量数据获取")
    print("=" * 60)

    try:
        from data_provider import DataFetcherManager

        manager = DataFetcherManager()

        # 测试多只股票
        stocks = ["600519", "000001", "300750"]
        results = {}

        for stock in stocks:
            try:
                df, source = manager.get_daily_data(stock, days=10)
                results[stock] = {
                    "rows": len(df),
                    "source": source,
                    "success": not df.empty,
                }
                status = "✅" if not df.empty else "⚠️"
                print(f"   {status} {stock}: {len(df)} 行, 来源: {source}")
            except Exception as e:
                results[stock] = {"success": False, "error": str(e)}
                print(f"   ❌ {stock}: {e}")

        success_count = sum(1 for r in results.values() if r.get("success"))
        print(f"\n   成功率: {success_count}/{len(stocks)}")
        return success_count > 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有端到端测试。"""
    print("🚀 SinaFetcher 端到端测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    tests = [
        ("DataFetcherManager 集成", test_data_fetcher_manager_integration),
        ("技术指标计算", test_technical_indicators),
        ("StockAnalyzer 集成", test_stock_analyzer_integration),
        ("批量数据获取", test_multi_stock_batch),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
            results.append((name, False))

    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")

    print(f"\n   总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！SinaFetcher 可以正常使用。")
    elif passed > 0:
        print("\n⚠️ 部分测试通过，SinaFetcher 基本可用。")
    else:
        print("\n❌ 所有测试失败，请检查配置。")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
