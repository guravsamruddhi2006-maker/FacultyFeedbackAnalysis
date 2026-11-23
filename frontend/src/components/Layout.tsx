import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BarChart3,
  BookOpen,
  ClipboardList,
  GraduationCap,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Menu,
  ScrollText,
  ShieldCheck,
  UserCog,
  UserRound,
  Users,
  X,
} from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { api, ApiError } from "@/lib/api";
import { cn, initials } from "@/lib/utils";
import { Button, Card, CardContent, Field, Modal, PasswordInput } from "@/components/ui";

const navByRole = {
  student: [{ to: "/student", label: "My feedback", icon: ClipboardList }],
  faculty: [
    { to: "/faculty", label: "Teaching overview", icon: LayoutDashboard },
    { to: "/faculty/subjects", label: "My subjects", icon: BookOpen },
    { to: "/faculty/comments", label: "Student comments", icon: ScrollText },
    { to: "/faculty/profile", label: "My profile", icon: UserRound },
  ],
  admin: [
    { to: "/admin", label: "Overview", icon: LayoutDashboard },
    { to: "/admin/analytics", label: "Analytics", icon: BarChart3 },
    { to: "/admin/faculty", label: "Faculty", icon: GraduationCap },
    { to: "/admin/students", label: "Students", icon: Users },
    { to: "/admin/catalog", label: "Catalog", icon: BookOpen },
    { to: "/admin/admins", label: "Administrators", icon: UserCog },
    { to: "/admin/audit", label: "Audit log", icon: ShieldCheck },
  ],
};

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white shadow-sm">
        <GraduationCap className="h-5 w-5" />
      </div>
      <p className="text-sm font-semibold leading-tight text-slate-900">FacultyInsight AI</p>
    </div>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { notify } = useToast();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [savingPassword, setSavingPassword] = useState(false);

  if (!user) return null;
  const items = navByRole[user.role] ?? [];

  const changePassword = async () => {
    setSavingPassword(true);
    try {
      await api("/auth/change-password", { method: "POST", body: passwords });
      notify("Password changed successfully.", "success");
      setPasswordOpen(false);
      setPasswords({ current_password: "", new_password: "", confirm_password: "" });
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "Could not change password.", "error");
    } finally {
      setSavingPassword(false);
    }
  };

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-5 py-5">
        <Brand />
        <button className="lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu">
          <X className="h-5 w-5 text-slate-500" />
        </button>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/admin" || item.to === "/faculty" || item.to === "/student"}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-primary"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t p-3">
        <div className="flex items-center gap-3 rounded-lg bg-slate-50 p-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
            {initials(user.name)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-900">{user.name}</p>
            <p className="truncate text-xs capitalize text-slate-500">{user.role}</p>
          </div>
        </div>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <Button variant="outline" size="sm" icon={<KeyRound className="h-3.5 w-3.5" />} onClick={() => setPasswordOpen(true)}>
            Password
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<LogOut className="h-3.5 w-3.5" />}
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-white lg:block">{sidebar}</aside>
      {mobileOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white shadow-xl">{sidebar}</aside>
        </div>
      ) : null}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b bg-white/90 px-4 backdrop-blur lg:hidden">
          <button onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu className="h-6 w-6 text-slate-600" />
          </button>
          <Brand />
          <div className="w-6" />
        </header>
        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>

      <Modal
        open={passwordOpen}
        title="Change password"
        description="Use at least 8 characters with a letter and a number."
        onClose={() => setPasswordOpen(false)}
        footer={
          <>
            <Button variant="outline" onClick={() => setPasswordOpen(false)}>
              Cancel
            </Button>
            <Button loading={savingPassword} onClick={changePassword}>
              Update password
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="Current password" htmlFor="current-password">
            <PasswordInput
              id="current-password"
              value={passwords.current_password}
              onChange={(event) => setPasswords({ ...passwords, current_password: event.target.value })}
            />
          </Field>
          <Field label="New password" htmlFor="new-password">
            <PasswordInput
              id="new-password"
              value={passwords.new_password}
              onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })}
            />
          </Field>
          <Field label="Confirm new password" htmlFor="confirm-password">
            <PasswordInput
              id="confirm-password"
              value={passwords.confirm_password}
              onChange={(event) => setPasswords({ ...passwords, confirm_password: event.target.value })}
            />
          </Field>
        </div>
      </Modal>
    </div>
  );
}

export function AuthShell({ children, title, subtitle }: { children: ReactNode; title: string; subtitle: string }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6">
      <div className="mb-6">
        <Brand />
      </div>
      <Card className="w-full max-w-md">
        <CardContent className="p-7">
          <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </CardContent>
      </Card>
    </div>
  );
}
