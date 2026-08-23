import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileQuestion, Home } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F5F7FA] flex items-center justify-center p-6 text-center">
      <div className="bg-white border border-gray-200 rounded-3xl p-8 shadow-lg max-w-md w-full">
        <div className="w-16 h-16 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <FileQuestion className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">404 — Page Not Found</h1>
        <p className="text-xs text-gray-600 mb-6">
          The requested Smart Bhopal resource or endpoint does not exist.
        </p>
        <Button onClick={() => navigate('/login')} leftIcon={<Home className="w-4 h-4" />}>
          Go to Main Gateway
        </Button>
      </div>
    </div>
  );
};
