import type React from 'react';
import { cn } from '../../utils/cn';

export interface TableColumn<T> {
  /** Unique column key (also used as the field accessor when no `render` is provided). */
  key: string;
  /** Header content. */
  header: React.ReactNode;
  /** Cell text alignment. */
  align?: 'left' | 'right' | 'center';
  /** Extra cell className. */
  className?: string;
  /** Custom cell renderer. */
  render?: (row: T, rowIndex: number) => React.ReactNode;
  /** Optional fixed column width (CSS value). */
  width?: string;
}

interface TableProps<T> {
  columns: Array<TableColumn<T>>;
  data: T[];
  /** Resolve a stable React key for each row. Defaults to the row index. */
  rowKey?: (row: T, index: number) => string | number;
  variant?: 'default' | 'bordered' | 'plain';
  density?: 'normal' | 'compact';
  /** Apply zebra striping to body rows. */
  striped?: boolean;
  onRowClick?: (row: T, index: number) => void;
  emptyText?: React.ReactNode;
  className?: string;
  wrapperClassName?: string;
}

/**
 * Token-driven, theme-aware table primitive.
 * Pair with `Tabs` for tabbed data views, or compose inside `Card`/`SectionCard`.
 */
export function Table<T>({
  columns,
  data,
  rowKey,
  variant = 'default',
  density = 'normal',
  striped = false,
  onRowClick,
  emptyText = '暂无数据',
  className,
  wrapperClassName,
}: TableProps<T>): React.ReactElement {
  const wrapperStyles = {
    default: 'rounded-2xl border border-border/70 bg-card shadow-soft-card overflow-hidden',
    bordered: 'rounded-2xl border border-border/70 bg-card overflow-hidden',
    plain: 'overflow-hidden',
  } as const;

  const cellPadding = density === 'compact' ? 'px-4 py-2' : 'px-4 py-3';

  const alignClass = (align?: 'left' | 'right' | 'center') =>
    align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : 'text-left';

  const clickable = Boolean(onRowClick);

  return (
    <div className={cn(wrapperStyles[variant], wrapperClassName)}>
      <table className={cn('w-full border-collapse text-sm', className)}>
        <thead>
          <tr className="border-b border-border/70 bg-hover/40">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                style={col.width ? { width: col.width } : undefined}
                className={cn(
                  cellPadding,
                  'font-medium text-secondary-text',
                  alignClass(col.align),
                  col.className,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={cn(cellPadding, 'text-center text-muted-text')}>
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowKey ? rowKey(row, rowIndex) : rowIndex}
                onClick={onRowClick ? () => onRowClick(row, rowIndex) : undefined}
                className={cn(
                  'border-b border-border/40 transition-colors',
                  striped && rowIndex % 2 === 1 ? 'bg-hover/30' : '',
                  clickable ? 'cursor-pointer hover:bg-hover' : '',
                )}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(cellPadding, 'text-foreground', alignClass(col.align), col.className)}
                  >
                    {col.render
                      ? col.render(row, rowIndex)
                      : (row as Record<string, React.ReactNode>)[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
