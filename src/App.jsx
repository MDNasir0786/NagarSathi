import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryProvider } from './app/QueryProvider.jsx';
import { AppRoutes } from './app/AppRoutes.jsx';
import { ErrorBoundary } from './components/feedback/ErrorBoundary.jsx';

export default function App() {
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
