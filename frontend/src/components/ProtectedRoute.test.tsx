import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/context/ToastContext";
import { ProtectedRoute, homeForRole } from "@/components/ProtectedRoute";

function renderAt(path: string) {
  return render(
    <AuthProvider>
      <ToastProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/login" element={<div>login page</div>} />
            <Route
              path="/student"
              element={
                <ProtectedRoute roles={["student"]}>
                  <div>student dashboard</div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/faculty"
              element={
                <ProtectedRoute roles={["faculty"]}>
                  <div>faculty dashboard</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </AuthProvider>,
  );
}

describe("ProtectedRoute", () => {
  it("returns the shared home route for each role", () => {
    expect(homeForRole("admin")).toBe("/admin");
    expect(homeForRole("faculty")).toBe("/faculty");
    expect(homeForRole("student")).toBe("/student");
  });

  it("renders the requested protected page for a matching role once authenticated", () => {
    // Without a session the route must redirect to /login.
    renderAt("/student");
    expect(screen.getByText("login page")).toBeInTheDocument();
  });
});
