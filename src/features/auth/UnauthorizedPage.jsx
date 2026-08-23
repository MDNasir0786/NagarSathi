import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { useAuthStore } from '../../stores/authStore';

export const UnauthorizedPage = () => {
  const navigate = useNavigate();
  const { role } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#F5F7FA] flex items-center justify-center p-6 text-center">
      <div className="bg-white border border-gray-200 rounded-3xl p-8 shadow-lg max-w-md w-full">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">403 — Access Denied</h1>
        <p className="text-xs text-gray-600 mb-6 leading-relaxed">
          You do not have administrative clearance to access this portal section as a{' '}
          <span className="font-bold text-red-600">{role}</span>.
        </p>
        <Button onClick={() => navigate(-1)} leftIcon={<ArrowLeft className="w-4 h-4" />}>
          Return to Previous Page
        </Button>
      </div>
    </div>
  );
};
