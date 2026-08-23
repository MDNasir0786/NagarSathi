import React from 'react';
import { clsx } from 'clsx';

export const Card = ({ children, className, hoverable = false, ...props }) => {
  return (
    <div
      className={clsx(
        'bg-white border border-gray-200 rounded-xl p-5 shadow-sm transition-all duration-200',
        hoverable && 'hover:shadow-md hover:-translate-y-0.5 cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
