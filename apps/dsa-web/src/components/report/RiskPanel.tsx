import type React from 'react';
import type { RiskProfile } from '../../types/analysis';
import { Card } from '../common';
import { DashboardPanelHeader } from '../dashboard';

interface RiskPanelProps {
  riskProfile?: RiskProfile;
}

/**
 * Trade-level risk analysis panel.
 * Displays ATR, position sizing, SL/TP, R:R ratio, and volatility regime.
 */
export const RiskPanel: React.FC<RiskPanelProps> = ({ riskProfile }) => {
  if (!riskProfile || riskProfile.passRiskFilter === undefined) {
    return null;
  }

  const formatPct = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatPrice = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return value.toFixed(2);
  };

  const volRegimeColor = (regime?: string): string => {
    switch (regime) {
      case 'low': return 'text-blue-500';
      case 'high': return 'text-red-500';
      default: return 'text-green-500';
    }
  };

  return (
    <Card variant="bordered" padding="md" className="home-panel-card text-left">
      <DashboardPanelHeader
        eyebrow="TRADE-LEVEL RISK"
        title="风险分析"
        className="mb-3"
      />
      <div className="space-y-3">
        {/* ATR */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-text">ATR</span>
            <div className="font-mono">
              {formatPrice(riskProfile.atr)} ({formatPct(riskProfile.atrPct)})
            </div>
          </div>
          <div>
            <span className="text-muted-text">波动率状态</span>
            <div className={`font-mono ${volRegimeColor(riskProfile.volRegime)}`}>
              {riskProfile.volRegime || 'N/A'}
              {riskProfile.volScaleApplied && ' (已缩放)'}
            </div>
          </div>
        </div>

        {/* Position Sizing */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-text">建议仓位</span>
            <div className="font-mono">
              {riskProfile.suggestedShares || 0} 股 ({formatPct(riskProfile.positionPct)})
            </div>
          </div>
          <div>
            <span className="text-muted-text">建议金额</span>
            <div className="font-mono">
              ¥{(riskProfile.suggestedAmount || 0).toLocaleString()}
            </div>
          </div>
        </div>

        {/* SL/TP */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-text">止损位</span>
            <div className="font-mono text-red-500">
              {formatPrice(riskProfile.stopLossPrice)} (-{formatPct(riskProfile.stopLossPct)})
            </div>
          </div>
          <div>
            <span className="text-muted-text">止盈位</span>
            <div className="font-mono text-green-500">
              {formatPrice(riskProfile.takeProfitPrice)} (+{formatPct(riskProfile.takeProfitPct)})
            </div>
          </div>
        </div>

        {/* R:R Ratio */}
        <div className="text-sm">
          <span className="text-muted-text">风险收益比</span>
          <div className={`font-mono font-bold ${(riskProfile.riskRewardRatio || 0) >= 2 ? 'text-green-500' : 'text-yellow-500'}`}>
            {riskProfile.riskRewardRatio?.toFixed(2) || 'N/A'}
          </div>
        </div>

        {/* Risk Filter Status */}
        <div className="text-sm">
          <span className="text-muted-text">风险过滤</span>
          <div className={riskProfile.passRiskFilter ? 'text-green-500' : 'text-red-500'}>
            {riskProfile.passRiskFilter ? '✅ 通过' : '❌ 未通过'}
            {riskProfile.riskFiltered && ' (已降级)'}
          </div>
          {riskProfile.riskBlockReasons && riskProfile.riskBlockReasons.length > 0 && (
            <div className="mt-1 text-xs text-yellow-600">
              {riskProfile.riskBlockReasons.join('; ')}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
