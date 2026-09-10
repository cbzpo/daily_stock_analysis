import type React from 'react';
import { cn } from '../../utils/cn';

export interface TabItem {
  key: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  activeKey: string;
  onChange: (key: string) => void;
  variant?: 'underline' | 'pill';
  className?: string;
  ariaLabel?: string;
}

/**
 * Token-driven tab switcher with `underline` (segmented border) and `pill`
 * (contained) variants. Fully keyboard accessible and theme-aware.
 */
export function Tabs({
  tabs,
  activeKey,
  onChange,
  variant = 'underline',
  className,
  ariaLabel,
}: TabsProps): React.ReactElement {
  if (variant === 'pill') {
    return (
      <div
        role="tablist"
        aria-label={ariaLabel}
        className={cn(
          'inline-flex flex-wrap gap-1 rounded-2xl border border-border/70 bg-hover/40 p-1',
          className,
        )}
      >
        {tabs.map((tab) => {
          const active = tab.key === activeKey;
          return (
            <button
              key={tab.key}
              type="button"
              role="tab"
              aria-selected={active}
              disabled={tab.disabled}
              onClick={() => !tab.disabled && onChange(tab.key)}
              className={cn(
                'inline-flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-sm font-medium transition-all',
                'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-cyan/15',
                'disabled:cursor-not-allowed disabled:opacity-50',
                active
                  ? 'bg-card text-foreground shadow-soft-card'
                  : 'text-secondary-text hover:bg-hover hover:text-foreground',
              )}
            >
              {tab.icon ? <span className="shrink-0">{tab.icon}</span> : null}
              {tab.label}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={cn('flex flex-wrap gap-1 border-b border-border/70', className)}
    >
      {tabs.map((tab) => {
        const active = tab.key === activeKey;
        return (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={tab.disabled}
            onClick={() => !tab.disabled && onChange(tab.key)}
            className={cn(
              'inline-flex items-center gap-2 border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors',
              'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-cyan/15 -mb-px',
              'disabled:cursor-not-allowed disabled:opacity-50',
              active
                ? 'border-primary text-foreground'
                : 'border-transparent text-secondary-text hover:border-border hover:text-foreground',
            )}
          >
            {tab.icon ? <span className="shrink-0">{tab.icon}</span> : null}
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
