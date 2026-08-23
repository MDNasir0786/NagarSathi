import React from 'react';
import { clsx } from 'clsx';

export const LoadingSkeleton = ({ count = 3, className = '' }) => {
  return (
    <div className="space-y-4 animate-pulse w-full">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={clsx('bg-slate-200/80 rounded-xl h-24 w-full', className)}
        />
      ))}
    </div>
  );
};
