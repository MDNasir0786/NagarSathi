import React from 'react';
import { clsx } from 'clsx';

export const StatCard = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  iconBgColor = 'bg-emerald-50 text-emerald-600',
  className,
}) => {
  return (
    <div className={clsx('bg-white border border-gray-200 rounded-xl p-5 shadow-sm', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</span>
        <div className={clsx('p-2.5 rounded-xl flex items-center justify-center', iconBgColor)}>
          {icon}
        </div>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {trend && (
          <span
            className={clsx(
              'text-xs font-medium px-2 py-0.5 rounded-full',
              trend.isPositive ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
    </div>
  );
};
