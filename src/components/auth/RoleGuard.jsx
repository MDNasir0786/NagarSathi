import React from 'react';
import { useAuthStore } from '../../stores/authStore';

export const RoleGuard = ({ children, allowedRoles, fallback = null }) => {
  const { role } = useAuthStore();
  if (allowedRoles && !allowedRoles.includes(role)) {
    return fallback;
  }
  return children;
};
