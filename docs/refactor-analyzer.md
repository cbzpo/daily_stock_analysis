# analyzer.py 拆分计划

## 当前状态

- 文件：`src/analyzer.py`
- 行数：4787 行
- 函数/类数量：51 个

## 逻辑分组（按行号范围）

### 1. utils.py (1-256行) - 通用工具函数
- `_localized_text` - 多语言文本选择
- `_normalize_risk_warning_values` - 风险警告标准化
- `_today_has_realtime_overlay` - 实时数据覆盖检测
- `_today_looks_complete_daily_bar` - 完整日线检测
- `_phase_aware_quote_labels` - 阶段感知报价标签
- `_should_hide_regular_session_ohlc` - 是否隐藏常规OHLC
- `_legacy_market_group` - 市场分组
- `_legacy_audit_marker_specs` - 审计标记规格
- `_LiteLLMStreamError` - 流式错误类
- `_AllModelsFailedError` - 所有模型失败异常

### 2. content_integrity.py (296-593行) - 内容完整性检查
- `check_content_integrity` - 检查必填字段
- `apply_placeholder_fill` - 填充占位符
- `_is_value_placeholder` - 值占位符检测
- `_is_meaningful_text` - 有意义文本检测
- `_safe_float` - 安全浮点转换

### 3. chip_structure.py (593-992行) - 筹码结构分析
- `_coerce_chip_metric` - 筹码指标转换
- `_derive_chip_health` - 筹码健康度推导
- `_build_chip_structure_from_data` - 构建筹码结构
- `_has_meaningful_chip_data` - 有意义筹码数据检测
- `_mark_chip_structure_unavailable` - 标记筹码不可用
- `normalize_chip_structure_availability` - 标准化筹码可用性
- `fill_chip_structure_if_needed` - 按需填充筹码
- `fill_price_position_if_needed` - 按需填充价格位置

### 4. decision_guard.py (992-1606行) - 决策护栏逻辑
- `_has_structural_risk_alert` - 结构性风险检测
- `_is_significant_structural_risk` - 显著结构性风险
- `_sync_stability_dashboard_fields` - 稳定性仪表盘字段同步
- `_as_dict_for_decision_guard` - 决策护栏字典转换
- `_first_list_value` - 首个列表值
- `_coerce_numeric_value` - 数值强制转换
- `_first_numeric_value` - 首个数值
- `_capital_flow_bias` - 资金流向偏差
- `_capital_flow_bias_with_status` - 带状态的资金流向偏差
- `_capital_flow_status_for_stability` - 稳定性资金状态
- `_set_decision_stability_unavailable` - 设置决策稳定性不可用
- `_record_decision_score_calibration` - 记录决策分数校准
- `_bound_hold_watch_sentiment_score` - 绑定持有/观望情绪分数
- `_apply_hold_watch_dashboard` - 应用持有/观望仪表盘
- `_downgrade_buy_without_capital_flow` - 无资金流降级买入
- `_downgrade_to_structural_hold` - 降级为结构性持有
- `_set_structural_hold_wording` - 设置结构性持有措辞
- `get_stock_name_multi_source` - 多源获取股票名称

### 5. analysis_result.py (1667-1860行) - AnalysisResult 数据类
- `AnalysisResult` - 分析结果数据类
- `populate_decision_action_fields` - 填充决策动作字段

### 6. gemini_analyzer.py (1860-4787行) - 核心 LLM 分析器
- `GeminiAnalyzer` - 主分析器类（约2900行）
  - `__init__` - 初始化
  - `_get_runtime_config` - 获取运行时配置
  - `_get_skill_prompt_sections` - 获取技能提示词段落
  - `_get_analysis_system_prompt` - 获取分析系统提示词
  - `_has_channel_config` - 检查渠道配置
  - `_init_litellm` - 初始化LiteLLM
  - `is_available` - 检查可用性
  - ... (更多方法)

### 7. __init__.py - 包入口
- `get_analyzer` - 工厂函数
- 重新导出所有公共接口

## 迁移步骤

### 阶段1：准备（不修改代码）
1. 备份 `src/analyzer.py` → `src/analyzer.py.bak` ✅
2. 创建 `docs/refactor-analyzer.md` ✅
3. 运行现有测试确保基准通过

### 阶段2：创建包结构
1. 创建 `src/analyzer/` 目录
2. 创建 `src/analyzer/__init__.py` - 导出所有公共接口
3. 创建 `src/analyzer/utils.py` - 工具函数
4. 创建 `src/analyzer/content_integrity.py` - 内容完整性
5. 创建 `src/analyzer/chip_structure.py` - 筹码结构
6. 创建 `src/analyzer/decision_guard.py` - 决策护栏
7. 创建 `src/analyzer/analysis_result.py` - 数据类
8. 创建 `src/analyzer/gemini_analyzer.py` - 核心分析器

### 阶段3：逐步迁移
1. 先迁移小模块（utils, content_integrity, chip_structure, decision_guard）
2. 验证每个模块的导入
3. 迁移 AnalysisResult 数据类
4. 最后迁移 GeminiAnalyzer（最大模块）

### 阶段4：验证
1. 运行所有测试
2. 手动测试股票分析功能
3. 确保向后兼容

## 风险点

1. **导入路径变化** - 其他模块使用 `from src.analyzer import xxx`
2. **循环导入** - 模块间可能存在循环依赖
3. **测试覆盖** - 需要确保测试覆盖所有路径

## 预期收益

- 每个文件不超过 600 行
- 职责单一，易于理解和维护
- 测试隔离性改善
- 为后续类型安全改造打下基础
