import { lazy, Suspense } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/Layout";
import { ProtectedRoute, homeForRole } from "@/components/ProtectedRoute";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { ToastProvider } from "@/context/ToastContext";
import { AdminSetupPage, LoginPage, RegisterPage } from "@/pages/AuthPages";
import { AboutPage, LandingPage } from "@/pages/Public";
import { Card, CardContent, LoadingBlock } from "@/components/ui";

const AdminDashboard = lazy(() => import("@/pages/admin/AdminDashboard").then((module) => ({ default: module.AdminDashboard })));
const AdminManagement = lazy(() => import("@/pages/admin/AdminManagement").then((module) => ({ default: module.AdminManagement })));
const FacultyDashboard = lazy(() => import("@/pages/faculty/FacultyDashboard").then((module) => ({ default: module.FacultyDashboard })));
const FacultyCommentsPage = lazy(() => import("@/pages/faculty/FacultyDashboard").then((module) => ({ default: module.FacultyCommentsPage })));
const FacultyProfile = lazy(() => import("@/pages/faculty/FacultyProfile").then((module) => ({ default: module.FacultyProfilePage })));
const FeedbackFormPage = lazy(() => import("@/pages/student/FeedbackForm").then((module) => ({ default: module.FeedbackFormPage })));
const StudentDashboard = lazy(() => import("@/pages/student/StudentDashboard").then((module) => ({ default: module.StudentDashboard })));

function HomeRedirect() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingBlock label="Checking your session…" />;
  if (user) return <Navigate to={homeForRole(user.role)} replace />;
  return <LandingPage />;
}

function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <Card className="w-full max-w-lg">
        <CardContent className="space-y-4 p-8 text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary">404</p>
          <h1 className="text-2xl font-semibold text-slate-900">Page not found</h1>
          <p className="text-sm text-slate-600">The page you requested does not exist.</p>
          <Link
            to="/"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-sm hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Return to FacultyInsight AI
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register/student" element={<RegisterPage kind="student" />} />
      <Route path="/register/faculty" element={<RegisterPage kind="faculty" />} />
      <Route path="/setup" element={<AdminSetupPage />} />
      <Route path="/setup/admin" element={<AdminSetupPage />} />

      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/analytics"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/faculty"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminManagement section="faculty" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/students"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminManagement section="students" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/catalog"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminManagement section="catalog" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/audit"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminManagement section="audit" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty"
          element={
            <ProtectedRoute roles={["faculty"]}>
              <FacultyDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty/profile"
          element={
            <ProtectedRoute roles={["faculty"]}>
              <FacultyProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty/comments"
          element={
            <ProtectedRoute roles={["faculty"]}>
              <FacultyCommentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student"
          element={
            <ProtectedRoute roles={["student"]}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/feedback/:offeringId"
          element={
            <ProtectedRoute roles={["student"]}>
              <FeedbackFormPage />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Suspense fallback={<LoadingBlock label="Loading your workspace…" />}>
            <AppRoutes />
          </Suspense>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}