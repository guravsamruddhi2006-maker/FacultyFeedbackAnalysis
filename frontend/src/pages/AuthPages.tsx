import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { GraduationCap, ShieldCheck, UserRound } from "lucide-react";

import { AuthShell } from "@/components/Layout";
import { homeForRole } from "@/components/ProtectedRoute";
import { Alert, Button, Field, Input, LoadingBlock, PasswordInput, Select } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { api, ApiError } from "@/lib/api";
import type { Department, Role } from "@/lib/types";

const passwordRule = z
  .string()
  .min(8, "Use at least 8 characters.")
  .regex(/[A-Za-z]/, "Include at least one letter.")
  .regex(/\d/, "Include at least one number.");

const loginSchema = z.object({
  identifier: z.string().min(1, "This field is required."),
  password: z.string().min(1, "Password is required."),
});
type LoginForm = z.infer<typeof loginSchema>;

const roleLabels: Record<Role, string> = {
  student: "Student",
  faculty: "Faculty",
  admin: "Administrator",
};

function isRole(value: unknown): value is Role {
  return value === "student" || value === "faculty" || value === "admin";
}

function useSetupCompleted() {
  const [completed, setCompleted] = useState<boolean | null>(null);
  useEffect(() => {
    let active = true;
    api<{ completed: boolean }>("/auth/setup-status")
      .then((status) => {
        if (active) setCompleted(status.completed);
      })
      .catch(() => {
        if (active) setCompleted(null);
      });
    return () => {
      active = false;
    };
  }, []);
  return completed;
}

export function LoginPage() {
  const { user, login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { notify } = useToast();
  const requestedRole = (location.state as { role?: unknown } | null)?.role;
  const [role, setRole] = useState<Role>(isRole(requestedRole) ? requestedRole : "student");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const setupCompleted = useSetupCompleted();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  useEffect(() => {
    if (user && !loading) {
      navigate(homeForRole(user.role), { replace: true });
    }
  }, [user, loading, navigate]);

  const onSubmit = async (values: LoginForm) => {
    setSubmitting(true);
    setError(null);
    try {
      const account = await login({ role, identifier: values.identifier.trim(), password: values.password });
      notify(`Welcome back, ${account.name}.`, "success");
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from && from !== "/login" ? from : homeForRole(account.role), { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to sign in. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const icons = { student: UserRound, faculty: GraduationCap, admin: ShieldCheck };

  return (
    <AuthShell title="Sign in" subtitle="Use your college account to continue.">
      <div className="mb-5 grid grid-cols-3 gap-1 rounded-lg bg-slate-100 p-1">
        {(Object.keys(roleLabels) as Role[]).map((item) => {
          const Icon = icons[item];
          return (
            <button
              key={item}
              type="button"
              onClick={() => {
                setRole(item);
                setError(null);
                setValue("identifier", "");
              }}
              className={`flex items-center justify-center gap-1.5 rounded-md px-2 py-2 text-xs font-medium transition ${
                role === item ? "bg-white text-primary shadow-sm" : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {roleLabels[item]}
            </button>
          );
        })}
      </div>

      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        {error ? <Alert variant="error">{error}</Alert> : null}
        {role === "admin" ? (
          <p className="text-xs text-slate-500">
            Administrator accounts are created during initial setup or by an existing administrator.
          </p>
        ) : null}
        <Field
          label={role === "student" ? "USN" : "Email address"}
          htmlFor="identifier"
          error={errors.identifier?.message}
        >
          <Input
            id="identifier"
            autoComplete={role === "student" ? "username" : "email"}
            placeholder={role === "student" ? "4UB26CS001" : "you@college.edu"}
            {...register("identifier")}
          />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password?.message}>
          <PasswordInput id="password" autoComplete="current-password" {...register("password")} />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={submitting}>
          Sign in as {roleLabels[role].toLowerCase()}
        </Button>
      </form>

      <div className="mt-5 space-y-2 border-t pt-4 text-center text-sm text-slate-500">
        <p>
          Student?{" "}
          <Link to="/register/student" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </p>
        <p>
          Faculty?{" "}
          <Link to="/register/faculty" className="font-medium text-primary hover:underline">
            Register for approval
          </Link>
        </p>
        {setupCompleted === false ? (
          <p>
            First time setting up the system?{" "}
            <Link to="/setup" className="font-medium text-primary hover:underline">
              Create the first admin
            </Link>
          </p>
        ) : null}
      </div>
    </AuthShell>
  );
}

const registerSchema = z
  .object({
    name: z.string().min(2, "Enter your full name."),
    identifier: z.string().min(6, "This field is required."),
    department_id: z.string().min(1, "Select your department."),
    password: passwordRule,
    confirm_password: z.string(),
  })
  .refine((values) => values.password === values.confirm_password, {
    path: ["confirm_password"],
    message: "Passwords do not match.",
  });
type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterPage({ kind }: { kind: "student" | "faculty" }) {
  const navigate = useNavigate();
  const { notify } = useToast();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [existingAccount, setExistingAccount] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  useEffect(() => {
    api<Department[]>("/catalog/public/departments")
      .then(setDepartments)
      .catch(() => setError("Could not load departments. Is the API running?"));
  }, []);

  const onSubmit = async (values: RegisterForm) => {
    setSubmitting(true);
    setError(null);
    setExistingAccount(false);
    try {
      const body =
        kind === "student"
          ? {
              student_id: values.identifier.trim().toUpperCase(),
              name: values.name.trim(),
              department_id: Number(values.department_id),
              password: values.password,
              confirm_password: values.confirm_password,
            }
          : {
              name: values.name.trim(),
              email: values.identifier.trim().toLowerCase(),
              department_id: Number(values.department_id),
              password: values.password,
              confirm_password: values.confirm_password,
            };
      const response = await api<{ message: string }>(`/auth/${kind}/register`, { method: "POST", body });
      notify(response.message, "success");
      navigate("/login", { state: { role: kind } });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed. Please try again.");
      setExistingAccount(err instanceof ApiError && err.status === 409);
    } finally {
      setSubmitting(false);
    }
  };

  const isStudent = kind === "student";
  return (
    <AuthShell
      title={isStudent ? "Create a student account" : "Faculty registration"}
      subtitle={
        isStudent
          ? "Sign up with your USN to submit course feedback."
          : "Your account becomes active after an administrator approves it."
      }
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        {error ? (
          <Alert variant="error">
            <p>{error}</p>
            {existingAccount ? (
              <p className="mt-1">
                <Link to="/login" state={{ role: kind }} className="font-medium underline">
                  Go to {isStudent ? "student" : "faculty"} sign in
                </Link>
              </p>
            ) : null}
          </Alert>
        ) : null}
        <Field label="Full name" htmlFor="name" error={errors.name?.message}>
          <Input id="name" placeholder="Your name" {...register("name")} />
        </Field>
        <Field
          label={isStudent ? "USN" : "Email address"}
          htmlFor="identifier"
          error={errors.identifier?.message}
        >
          <Input
            id="identifier"
            placeholder={isStudent ? "4UB26CS001" : "you@college.edu"}
            {...register("identifier")}
          />
        </Field>
        <Field label="Department" htmlFor="department_id" error={errors.department_id?.message}>
          <Select id="department_id" defaultValue="" {...register("department_id")}>
            <option value="" disabled>
              Select department
            </option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name} ({department.code})
              </option>
            ))}
          </Select>
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Password" htmlFor="password" error={errors.password?.message}>
            <PasswordInput id="password" autoComplete="new-password" {...register("password")} />
          </Field>
          <Field label="Confirm password" htmlFor="confirm_password" error={errors.confirm_password?.message}>
            <PasswordInput
              id="confirm_password"
              autoComplete="new-password"
              {...register("confirm_password")}
            />
          </Field>
        </div>
        <Button type="submit" className="w-full" size="lg" loading={submitting}>
          {isStudent ? "Create account" : "Submit registration"}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-500">
        Already registered?{" "}
        <Link to="/login" state={{ role: kind }} className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}

const setupSchema = z
  .object({
    name: z.string().min(2, "Enter your name."),
    email: z.string().email("Enter a valid email address."),
    password: passwordRule,
    confirm_password: z.string(),
  })
  .refine((values) => values.password === values.confirm_password, {
    path: ["confirm_password"],
    message: "Passwords do not match.",
  });
type SetupForm = z.infer<typeof setupSchema>;

type SetupState = "checking" | "open" | "completed" | "error";

export function AdminSetupPage() {
  const { user, loading: authLoading, setupAdmin } = useAuth();
  const navigate = useNavigate();
  const { notify } = useToast();
  const [state, setState] = useState<SetupState>("checking");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SetupForm>({ resolver: zodResolver(setupSchema) });

  useEffect(() => {
    let active = true;
    api<{ completed: boolean }>("/auth/setup-status")
      .then((status) => {
        if (active) setState(status.completed ? "completed" : "open");
      })
      .catch(() => {
        if (active) setState("error");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!authLoading && user) {
      navigate(homeForRole(user.role), { replace: true });
    }
  }, [user, authLoading, navigate]);

  const onSubmit = async (values: SetupForm) => {
    setSubmitting(true);
    setError(null);
    try {
      await setupAdmin({
        name: values.name.trim(),
        email: values.email.trim().toLowerCase(),
        password: values.password,
        confirm_password: values.confirm_password,
      });
      notify("Administrator account created.", "success");
      navigate("/admin", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setState("completed");
      }
      setError(err instanceof ApiError ? err.message : "Setup failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (state === "checking") {
    return (
      <AuthShell title="First admin setup" subtitle="Checking whether setup is still required.">
        <LoadingBlock label="Checking setup status…" />
      </AuthShell>
    );
  }

  if (state === "completed") {
    return (
      <AuthShell
        title="Setup already completed"
        subtitle="An administrator account already exists. Sign in with your administrator account."
      >
        <Link to="/login" state={{ role: "admin" }} className="block">
          <Button className="w-full" size="lg">
            Go to sign in
          </Button>
        </Link>
      </AuthShell>
    );
  }

  if (state === "error") {
    return (
      <AuthShell title="First admin setup" subtitle="Setup status could not be checked.">
        <div className="space-y-4">
          <Alert variant="error">The server could not be reached. Please try again.</Alert>
          <Button className="w-full" size="lg" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="First admin setup"
      subtitle="This one-time form creates the initial administrator. Later admins are created from inside the app."
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        {error ? <Alert variant="error">{error}</Alert> : null}
        <Field label="Full name" htmlFor="name" error={errors.name?.message}>
          <Input id="name" placeholder="Administrator name" {...register("name")} />
        </Field>
        <Field label="Email address" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" placeholder="admin@college.edu" {...register("email")} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Password" htmlFor="password" error={errors.password?.message}>
            <PasswordInput id="password" autoComplete="new-password" {...register("password")} />
          </Field>
          <Field label="Confirm password" htmlFor="confirm_password" error={errors.confirm_password?.message}>
            <PasswordInput
              id="confirm_password"
              autoComplete="new-password"
              {...register("confirm_password")}
            />
          </Field>
        </div>
        <Button type="submit" className="w-full" size="lg" loading={submitting}>
          Create administrator
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-500">
        Setup already completed?{" "}
        <Link to="/login" state={{ role: "admin" }} className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
