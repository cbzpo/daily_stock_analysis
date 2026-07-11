# -*- coding: utf-8 -*-
"""
GeminiAnalyzer 回归锚点测试

目的：为 analyzer.py 拆分提供快速验证基线
覆盖：初始化、可用性检查、核心数据结构、导入兼容性
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAnalyzerImports:
    """测试导入兼容性 - 确保拆分后导入路径不变"""

    def test_import_analyzer_module(self):
        """能从 src.analyzer 导入模块"""
        import src.analyzer
        assert src.analyzer is not None

    def test_import_gemini_analyzer(self):
        """能导入 GeminiAnalyzer 类"""
        from src.analyzer import GeminiAnalyzer
        assert GeminiAnalyzer is not None

    def test_import_analysis_result(self):
        """能导入 AnalysisResult 数据类"""
        from src.analyzer import AnalysisResult
        assert AnalysisResult is not None

    def test_import_get_analyzer(self):
        """能导入 get_analyzer 工厂函数"""
        from src.analyzer import get_analyzer
        assert callable(get_analyzer)

    def test_import_check_content_integrity(self):
        """能导入 check_content_integrity 函数"""
        from src.analyzer import check_content_integrity
        assert callable(check_content_integrity)

    def test_import_stabilize_decision_with_structure(self):
        """能导入 stabilize_decision_with_structure 函数"""
        from src.analyzer import stabilize_decision_with_structure
        assert callable(stabilize_decision_with_structure)


class TestAnalysisResult:
    """测试 AnalysisResult 数据结构"""

    def test_create_result_minimal(self):
        """能创建最小 AnalysisResult"""
        from src.analyzer import AnalysisResult
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=65,
            trend_prediction="震荡",
            operation_advice="观望",
        )
        assert result.code == "600519"
        assert result.name == "贵州茅台"
        assert result.sentiment_score == 65
        assert result.decision_type == "hold"  # 默认值

    def test_result_to_dict(self):
        """AnalysisResult.to_dict() 返回正确字典"""
        from src.analyzer import AnalysisResult
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=65,
            trend_prediction="震荡",
            operation_advice="观望",
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["code"] == "600519"
        assert d["sentiment_score"] == 65
        assert "dashboard" in d

    def test_result_get_emoji(self):
        """AnalysisResult.get_emoji() 返回有效 emoji"""
        from src.analyzer import AnalysisResult
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=65,
            trend_prediction="震荡",
            operation_advice="观望",
        )
        emoji = result.get_emoji()
        assert isinstance(emoji, str)
        assert len(emoji) > 0

    def test_result_with_dashboard(self):
        """带 dashboard 的 AnalysisResult 正常工作"""
        from src.analyzer import AnalysisResult
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=65,
            trend_prediction="震荡",
            operation_advice="观望",
            dashboard={
                "core_conclusion": {"one_sentence": "短线震荡，观望为主"},
                "intelligence": {"risk_alerts": ["风险1"]},
                "battle_plan": {"sniper_points": {"stop_loss": "1180"}},
            },
        )
        assert result.get_core_conclusion() == "短线震荡，观望为主"
        assert len(result.get_risk_alerts()) == 1
        assert result.get_sniper_points().get("stop_loss") == "1180"


class TestContentIntegrity:
    """测试内容完整性检查"""

    def test_check_passes_valid_result(self):
        """有效结果通过完整性检查"""
        from src.analyzer import AnalysisResult, check_content_integrity
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=65,
            trend_prediction="震荡",
            operation_advice="观望",
            analysis_summary="测试摘要",
            dashboard={
                "core_conclusion": {"one_sentence": "测试结论"},
                "intelligence": {"risk_alerts": ["风险"]},
                "battle_plan": {"sniper_points": {"stop_loss": "1180"}},
            },
        )
        passed, missing = check_content_integrity(result)
        assert passed is True
        assert len(missing) == 0

    def test_check_fails_missing_fields(self):
        """缺少必填字段时检查失败"""
        from src.analyzer import AnalysisResult, check_content_integrity
        result = AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=None,  # 缺少
            trend_prediction="震荡",
            operation_advice="",  # 空
            analysis_summary="",  # 空
        )
        passed, missing = check_content_integrity(result)
        assert passed is False
        assert "sentiment_score" in missing
        assert "operation_advice" in missing


class TestGeminiAnalyzerInit:
    """测试 GeminiAnalyzer 初始化"""

    def test_init_without_config(self):
        """无配置时能初始化（可能不可用）"""
        from src.analyzer import GeminiAnalyzer
        analyzer = GeminiAnalyzer()
        assert analyzer is not None

    def test_init_with_mock_config(self):
        """有配置时能初始化"""
        from src.analyzer import GeminiAnalyzer
        from src.config import Config
        mock_config = MagicMock(spec=Config)
        mock_config.litellm_model = ""
        analyzer = GeminiAnalyzer(config=mock_config)
        assert analyzer is not None


class TestDecisionGuard:
    """测试决策护栏函数"""

    def test_normalize_risk_warning_values_string(self):
        """字符串风险警告标准化"""
        from src.analyzer import _normalize_risk_warning_values
        result = _normalize_risk_warning_values("测试风险")
        assert result == ["测试风险"]

    def test_normalize_risk_warning_values_list(self):
        """列表风险警告标准化"""
        from src.analyzer import _normalize_risk_warning_values
        result = _normalize_risk_warning_values(["风险1", "风险2"])
        assert result == ["风险1", "风险2"]

    def test_normalize_risk_warning_values_none(self):
        """None 风险警告标准化"""
        from src.analyzer import _normalize_risk_warning_values
        result = _normalize_risk_warning_values(None)
        assert result == []

    def test_is_meaningful_text(self):
        """有意义文本检测"""
        from src.analyzer import _is_meaningful_text
        assert _is_meaningful_text("正常文本") is True
        assert _is_meaningful_text("") is False
        assert _is_meaningful_text(None) is False
        assert _is_meaningful_text("N/A") is False
