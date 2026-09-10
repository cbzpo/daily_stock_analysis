# -*- coding: utf-8 -*-
"""
修复持仓数量：将所有持仓数量除以 100（去掉两个零）

使用方法：
    python scripts/fix_portfolio_quantity_simple.py [--dry-run]

--dry-run: 仅显示将要修改的数据，不实际执行修改
"""

import argparse
import os
import sqlite3
from pathlib import Path


def fix_portfolio_quantity(dry_run: bool = False) -> None:
    """修复持仓数量，将所有数量除以 100"""
    # 数据库路径
    db_path = Path(__file__).resolve().parent.parent / "data" / "stock_analysis.db"
    
    if not db_path.exists():
        print(f"错误：数据库文件不存在: {db_path}")
        return
    
    print(f"数据库路径: {db_path}")
    print(f"模式: {'预览模式 (dry-run)' if dry_run else '执行模式'}")
    print("-" * 60)
    
    # 连接数据库
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 1. 检查 portfolio_positions 表
        print("\n[1/4] 检查 portfolio_positions 表...")
        cursor.execute("SELECT COUNT(*) FROM portfolio_positions")
        count = cursor.fetchone()[0]
        print(f"  找到 {count} 条持仓记录")
        
        if count == 0:
            print("  没有需要修复的持仓记录")
            return
        
        # 显示修复前的数据
        print("\n修复前的持仓数据（前 10 条）:")
        cursor.execute("""
            SELECT id, symbol, quantity, avg_cost, total_cost, market_value_base 
            FROM portfolio_positions 
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  ID={row[0]}, 代码={row[1]}, 数量={row[2]}, "
                  f"均价={row[3]}, 总成本={row[4]}, 市值={row[5]}")
        
        if not dry_run:
            # 2. 修复 portfolio_positions 表
            print("\n[2/4] 修复 portfolio_positions...")
            cursor.execute("""
                UPDATE portfolio_positions 
                SET quantity = quantity / 100.0,
                    total_cost = total_cost / 100.0,
                    market_value_base = market_value_base / 100.0,
                    unrealized_pnl_base = unrealized_pnl_base / 100.0
            """)
            print(f"  已修复 {cursor.rowcount} 条持仓记录")
            
            # 3. 修复 portfolio_position_lots 表
            print("\n[3/4] 修复 portfolio_position_lots...")
            cursor.execute("SELECT COUNT(*) FROM portfolio_position_lots")
            lots_count = cursor.fetchone()[0]
            print(f"  找到 {lots_count} 条持仓批次记录")
            
            if lots_count > 0:
                cursor.execute("""
                    UPDATE portfolio_position_lots 
                    SET remaining_quantity = remaining_quantity / 100.0,
                        unit_cost = unit_cost / 100.0
                """)
                print(f"  已修复 {cursor.rowcount} 条持仓批次记录")
            
            # 4. 修复 portfolio_trades 表
            print("\n[4/4] 修复 portfolio_trades...")
            cursor.execute("SELECT COUNT(*) FROM portfolio_trades")
            trades_count = cursor.fetchone()[0]
            print(f"  找到 {trades_count} 条交易记录")
            
            if trades_count > 0:
                cursor.execute("""
                    UPDATE portfolio_trades 
                    SET quantity = quantity / 100.0
                """)
                print(f"  已修复 {cursor.rowcount} 条交易记录")
            
            # 提交事务
            conn.commit()
            print("\n" + "=" * 60)
            print("修复完成！所有持仓数量已除以 100")
        else:
            print("\n" + "=" * 60)
            print("预览模式：未执行任何修改")
            print("如需执行，请移除 --dry-run 参数重新运行")
        
        # 显示修复后的数据
        print("\n修复后的持仓数据（前 10 条）:")
        cursor.execute("""
            SELECT id, symbol, quantity, avg_cost, total_cost, market_value_base 
            FROM portfolio_positions 
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  ID={row[0]}, 代码={row[1]}, 数量={row[2]}, "
                  f"均价={row[3]}, 总成本={row[4]}, 市值={row[5]}")
    
    except Exception as e:
        print(f"\n错误：{e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="修复持仓数量：将所有持仓数量除以 100")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要修改的数据，不实际执行修改")
    args = parser.parse_args()
    
    fix_portfolio_quantity(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
