# -*- coding: utf-8 -*-
"""修复 300059 均价为 20.07"""

import sqlite3
import shutil

db_path = r'Z:\data\stock_analysis.db'
backup_path = r'Z:\data\stock_analysis_backup.db'

shutil.copy2(db_path, backup_path)

conn = sqlite3.connect(backup_path, timeout=10)
cursor = conn.cursor()

# 更新 portfolio_positions
cursor.execute(
    "UPDATE portfolio_positions SET avg_cost = 20.07, total_cost = quantity * 20.07 WHERE symbol = '300059'"
)
print(f"已修复 portfolio_positions: {cursor.rowcount} 条")

# 更新 portfolio_position_lots
cursor.execute(
    "UPDATE portfolio_position_lots SET unit_cost = 20.07 WHERE symbol = '300059'"
)
print(f"已修复 portfolio_position_lots: {cursor.rowcount} 条")

# 更新 portfolio_trades（买入均价也修正）
cursor.execute(
    "UPDATE portfolio_trades SET price = 20.07 WHERE symbol = '300059' AND side = 'buy'"
)
print(f"已修复 portfolio_trades: {cursor.rowcount} 条")

conn.commit()

# 验证
cursor.execute("SELECT symbol, quantity, avg_cost, total_cost, market_value_base FROM portfolio_positions")
print("\n全部持仓:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:,.0f}股, 均价{row[2]:.2f}, 总成本{row[3]:,.0f}, 市值{row[4]:,.0f}")

conn.close()
shutil.copy2(backup_path, db_path)
print("\n已更新数据库")
