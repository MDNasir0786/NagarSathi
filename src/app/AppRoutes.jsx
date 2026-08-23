import React, { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { DashboardShell } from "../components/layout/DashboardShell";
import { LoginPage } from "../features/auth/LoginPage";
import { NGORegistration } from "../features/auth/NGORegistration";
import { UnauthorizedPage } from "../features/auth/UnauthorizedPage";
import { NotFoundPage } from "../features/auth/NotFoundPage";
import { LoadingSkeleton } from "../components/feedback/LoadingSkeleton";
import { RegisterPage } from "@/features/auth/RegisterPage";

// Lazy-loaded Feature Modules
const CitizenDashboard = lazy(
  () => import("../features/citizen/CitizenDashboard"),
);
const RegisterComplaint = lazy(
  () => import("../features/citizen/RegisterComplaint"),
);
const ComplaintTracking = lazy(
  () => import("../features/citizen/ComplaintTracking"),
);
const CitizenHistory = lazy(() => import("../features/citizen/CitizenHistory"));
const RewardsPage = lazy(() => import("../features/citizen/RewardsPage"));
const CitizenProfile = lazy(() => import("../features/citizen/CitizenProfile"));

const WorkerDashboard = lazy(
  () => import("../features/worker/WorkerDashboard"),
);
const WorkerTaskList = lazy(() => import("../features/worker/WorkerTaskList"));
const WorkerTaskDetail = lazy(
  () => import("../features/worker/WorkerTaskDetail"),
);
const WorkerCompleted = lazy(
  () => import("../features/worker/WorkerCompleted"),
);
const WorkerRewards = lazy(() => import("../features/worker/WorkerRewards"));

const NodalDashboard = lazy(
  () => import("../features/nodal-officer/NodalDashboard"),
);
const NodalRequests = lazy(
  () => import("../features/nodal-officer/NodalRequests"),
);
const NodalAssignments = lazy(
  () => import("../features/nodal-officer/NodalAssignments"),
);
const NodalWorkers = lazy(
  () => import("../features/nodal-officer/NodalWorkers"),
);
const NodalReports = lazy(
  () => import("../features/nodal-officer/NodalReports"),
);

const NGODashboard = lazy(() => import("../features/ngo/NGODashboard"));
const NGOAreas = lazy(() => import("../features/ngo/NGOAreas"));
const NGOComplaints = lazy(() => import("../features/ngo/NGOComplaints"));
const NGOVolunteers = lazy(() => import("../features/ngo/NGOVolunteers"));
const NGOEvents = lazy(() => import("../features/ngo/NGOEvents"));
const NGODonations = lazy(() => import("../features/ngo/NGODonations"));

const HigherAuthorityDashboard = lazy(
  () => import("../features/authority/HigherAuthorityDashboard"),
);
const AuthorityAnalytics = lazy(
  () => import("../features/authority/AuthorityAnalytics"),
);
const AuthorityEscalations = lazy(
  () => import("../features/authority/AuthorityEscalations"),
);
const AuthorityNGOPerformance = lazy(
  () => import("../features/authority/AuthorityNGOPerformance"),
);
const AuthorityWorkerPerformance = lazy(
  () => import("../features/authority/AuthorityWorkerPerformance"),
);

const AdminDashboard = lazy(() => import("../features/admin/AdminDashboard"));
const AdminUserManagement = lazy(
  () => import("../features/admin/AdminUserManagement"),
);
const AdminRolePermissions = lazy(
  () => import("../features/admin/AdminRolePermissions"),
);
const AdminAuditLogs = lazy(() => import("../features/admin/AdminAuditLogs"));
const AdminSettings = lazy(() => import("../features/admin/AdminSettings"));

const HelpSupportPage = lazy(() => import("../features/help/HelpSupportPage"));

const RouteFallback = () => (
  <div className="p-6 max-w-4xl mx-auto">
    <LoadingSkeleton count={3} />
  </div>
);

export const AppRoutes = () => {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        {/* Public Gateway */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/ngo/register" element={<NGORegistration />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        {/* Citizen Routes */}
        <Route
          path="/citizen"
          element={
            <ProtectedRoute allowedRoles={["CITIZEN", "SUPER_ADMIN"]}>
              <DashboardShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<CitizenDashboard />} />
          <Route path="complaints/new" element={<RegisterComplaint />} />
          <Route path="complaints" element={<ComplaintTracking />} />
          <Route path="history" element={<CitizenHistory />} />
          <Route path="rewards" element={<RewardsPage />} />
          <Route path="profile" element={<CitizenProfile />} />
        </Route>

        {/* Worker Routes */}
        <Route
          path="/worker"
          element={
            <ProtectedRoute allowedRoles={["WORKER", "SUPER_ADMIN"]}>
              <DashboardShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<WorkerDashboard />} />
          <Route path="tasks" element={<WorkerTaskList />} />
          <Route path="tasks/:id" element={<WorkerTaskDetail />} />
          <Route path="completed" element={<WorkerCompleted />} />
          <Route path="rewards" element={<WorkerRewards />} />
          <Route path="profile" element={<CitizenProfile />} />
        </Route>

        {/* Nodal Officer Routes */}
        <Route
          path="/nodal"
          element={
            <ProtectedRoute allowedRoles={["NODAL_OFFICER", "SUPER_ADMIN"]}>
              <DashboardShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<NodalDashboard />} />
          <Route path="requests" element={<NodalRequests />} />
          <Route path="assignments" element={<NodalAssignments />} />
          <Route path="workers" element={<NodalWorkers />} />
          <Route path="reports" element={<NodalReports />} />
        </Route>

        {/* NGO Routes */}
        <Route
          path="/ngo"
          element={
            <ProtectedRoute allowedRoles={["NGO", "SUPER_ADMIN"]}>
              <DashboardShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<NGODashboard />} />
          <Route path="areas" element={<NGOAreas />} />
          <Route path="complaints" element={<NGOComplaints />} />
          <Route path="volunteers" element={<NGOVolunteers />} />
          <Route path="events" element={<NGOEvents />} />
          <Route path="donations" element={<NGODonations />} />
        </Route>

        {/* Higher Authority Routes */}
        <Route
          path="/authority"
          element={
            <ProtectedRoute allowedRoles={["HIGHER_AUTHORITY", "SUPER_ADMIN"]}>
              <DashboardShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<HigherAuthorityDashboard />} />
          <Route path="analytics" element={<AuthorityAnalytics />} />
          <Route path="escalations" element={<AuthorityEscalations />} />
          <Route path="ngo-performance" element={<AuthorityNGOPerformance />} />
          <Route
            path="worker-performance"
            element={<AuthorityWorkerPerformance />}
          />
        </Route>

        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
              <DashboardShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<AdminUserManagement />} />
          <Route path="roles" element={<AdminRolePermissions />} />
          <Route path="audit-logs" element={<AdminAuditLogs />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>

        {/* Shared Routes */}
        <Route
          path="/help"
          element={
            <ProtectedRoute>
              <DashboardShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<HelpSupportPage />} />
        </Route>

        {/* 404 Fallback */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
};
