import React from 'react';
import { clsx } from 'clsx';
import { ChevronRight } from 'lucide-react';

export const ActionCard = ({
  title,
  description,
  icon,
  onClick,
  badge,
  className,
}) => {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'group bg-white border border-gray-200 hover:border-emerald-500 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer flex items-center justify-between',
        className
      )}
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white rounded-xl transition-colors">
          {icon}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors">{title}</h3>
            {badge && <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-medium">{badge}</span>}
          </div>
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{description}</p>
        </div>
      </div>
      <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
    </div>
  );
};
