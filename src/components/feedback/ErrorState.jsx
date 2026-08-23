import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '../ui/Button';

export const ErrorState = ({
  title = 'Something went wrong',
  message = 'Failed to load data. Please check your network connection and try again.',
  onRetry,
}) => {
  return (
    <div className="bg-red-50/50 border border-red-200 rounded-2xl p-6 text-center max-w-md mx-auto my-6">
      <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-bold text-red-900 mb-1">{title}</h3>
      <p className="text-xs text-red-700 mb-4">{message}</p>
      {onRetry && (
        <Button variant="danger" size="sm" onClick={onRetry} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
          Retry Action
        </Button>
      )}
    </div>
  );
};
