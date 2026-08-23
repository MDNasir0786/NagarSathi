import React from 'react';
import { clsx } from 'clsx';

export const StatusBadge = ({ status, className }) => {
  const getStyles = () => {
    switch (status) {
      case 'Submitted':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'In Review':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Assigned':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'In Progress':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'Completed':
      case 'Verified':
      case 'Closed':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Escalated':
        return 'bg-red-50 text-red-700 border-red-200 animate-pulse';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border',
        getStyles(),
        className
      )}
    >
      {status}
    </span>
  );
};
