import React, { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryProvider } from './app/QueryProvider.jsx';
import { AppRoutes } from './app/AppRoutes.jsx';
import { ErrorBoundary } from './components/feedback/ErrorBoundary.jsx';
import { useAuthStore } from './stores/authStore';

export default function App() {
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <ErrorBoundary>
      <QueryProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </QueryProvider>
    </ErrorBoundary>
  );
}
