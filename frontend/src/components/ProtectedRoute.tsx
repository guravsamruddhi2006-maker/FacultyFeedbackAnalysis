import type { ReactNode } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/context/AuthContext";
import { LoadingBlock } from "@/components/ui";
import type { Role } from "@/lib/types";

export function homeForRole(role: Role) {
  return role === "admin" ? "/admin" : role === "faculty" ? "/faculty" : "/student";
}

export function ProtectedRoute({ roles, children }: { roles?: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <LoadingBlock label="Checking your session…" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) {
    return (
      <main className="flex min-h-[50vh] flex-col items-center justify-center gap-4 text-center">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Access denied</h1>
          <p className="mt-2 text-sm text-slate-600">
            Your {user.role} account does not have permission to view this page.
          </p>
        </div>
        <Link
          to={homeForRole(user.role)}
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-sm hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          Return to your dashboard
        </Link>
      </main>
    );
  }
  return <>{children}</>;
}
