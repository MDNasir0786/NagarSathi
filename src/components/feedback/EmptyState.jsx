import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from '../ui/Button';

export const EmptyState = ({
  title = 'No records found',
  description = 'There are no active items matching your current criteria.',
  icon: Icon = Inbox,
  actionLabel,
  onAction,
}) => {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center max-w-md mx-auto my-6 shadow-sm">
      <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-gray-900 mb-1">{title}</h3>
      <p className="text-xs text-gray-500 mb-5 leading-relaxed">{description}</p>
      {actionLabel && onAction && (
        <Button onClick={onAction} size="sm">
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
