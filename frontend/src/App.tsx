import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { FDRListPage } from './pages/FDRListPage';
import { FDRDetailPage } from './pages/FDRDetailPage';
import { FDRCreatePage } from './pages/FDRCreatePage';
import { FDRUploadPage } from './pages/FDRUploadPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { RenewalWorkflowPage } from './pages/RenewalWorkflowPage';
import { ReleaseWorkflowPage } from './pages/ReleaseWorkflowPage';
import { InstitutionsPage } from './pages/InstitutionsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { DatasetManagementPage } from './pages/DatasetManagementPage';
import { MFASetupPage } from './pages/MFASetupPage';
import { UserRole } from './types';

const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: UserRole[] }> = ({
  children,
  allowedRoles
}) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-xs font-semibold">
        Verifying security credentials...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="fdrs" element={<FDRListPage />} />
            <Route path="fdrs/create" element={<FDRCreatePage />} />
            <Route path="fdrs/:id" element={<FDRDetailPage />} />
            <Route path="fdrs/:id/upload" element={<FDRUploadPage />} />
            <Route
              path="review-queue"
              element={
                <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'REVIEWING_OFFICIAL']}>
                  <ReviewQueuePage />
                </ProtectedRoute>
              }
            />
            <Route path="renewals" element={<RenewalWorkflowPage />} />
            <Route path="releases" element={<ReleaseWorkflowPage />} />
            <Route path="institutions" element={<InstitutionsPage />} />
            <Route
              path="audit-logs"
              element={
                <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'READONLY_AUDITOR']}>
                  <AuditLogsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="datasets"
              element={
                <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                  <DatasetManagementPage />
                </ProtectedRoute>
              }
            />
            <Route path="mfa-setup" element={<MFASetupPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
