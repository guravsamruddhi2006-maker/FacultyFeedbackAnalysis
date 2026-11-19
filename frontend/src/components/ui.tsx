// import {
//   forwardRef,
//   type ButtonHTMLAttributes,
//   type HTMLAttributes,
//   type InputHTMLAttributes,
//   type ReactNode,
//   type SelectHTMLAttributes,
//   type TextareaHTMLAttributes,
// } from "react";
// import { AlertCircle, Inbox, Loader2, X } from "lucide-react";

// import { cn } from "@/lib/utils";

// type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "destructive";
// type ButtonSize = "sm" | "md" | "lg" | "icon";

// const buttonVariants: Record<ButtonVariant, string> = {
//   primary: "bg-primary text-primary-foreground hover:bg-blue-700 shadow-sm",
//   secondary: "bg-secondary text-secondary-foreground hover:bg-slate-200",
//   outline: "border border-input bg-white hover:bg-slate-50",
//   ghost: "hover:bg-slate-100 text-slate-700",
//   destructive: "bg-destructive text-destructive-foreground hover:bg-red-700 shadow-sm",
// };

// const buttonSizes: Record<ButtonSize, string> = {
//   sm: "h-8 px-3 text-xs",
//   md: "h-10 px-4 text-sm",
//   lg: "h-11 px-6 text-sm",
//   icon: "h-9 w-9",
// };

// export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
//   variant?: ButtonVariant;
//   size?: ButtonSize;
//   loading?: boolean;
//   icon?: ReactNode;
// }

// export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
//   ({ className, variant = "primary", size = "md", loading, icon, children, disabled, ...props }, ref) => (
//     <button
//       ref={ref}
//       disabled={disabled || loading}
//       className={cn(
//         "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-60",
//         buttonVariants[variant],
//         buttonSizes[size],
//         className,
//       )}
//       {...props}
//     >
//       {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
//       {children}
//     </button>
//   ),
// );
// Button.displayName = "Button";

// export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
//   return <div className={cn("rounded-xl border bg-card text-card-foreground shadow-sm", className)} {...props} />;
// }

// export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
//   return <div className={cn("flex flex-col gap-1 border-b px-5 py-4", className)} {...props} />;
// }

// export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
//   return <div className={cn("p-5", className)} {...props} />;
// }

// export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
//   return <h3 className={cn("text-base font-semibold text-slate-900", className)} {...props} />;
// }

// export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
//   return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
// }

// export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
//   ({ className, ...props }, ref) => (
//     <input
//       ref={ref}
//       className={cn(
//         "flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
//         className,
//       )}
//       {...props}
//     />
//   ),
// );
// Input.displayName = "Input";

// export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
//   ({ className, ...props }, ref) => (
//     <textarea
//       ref={ref}
//       className={cn(
//         "flex min-h-[96px] w-full rounded-md border border-input bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
//         className,
//       )}
//       {...props}
//     />
//   ),
// );
// Textarea.displayName = "Textarea";

// export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
//   ({ className, ...props }, ref) => (
//     <select
//       ref={ref}
//       className={cn(
//         "flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
//         className,
//       )}
//       {...props}
//     />
//   ),
// );
// Select.displayName = "Select";

// export function Label({ className, ...props }: HTMLAttributes<HTMLLabelElement>) {
//   return <label className={cn("text-sm font-medium text-slate-700", className)} {...props} />;
// }

// export function Field({
//   label,
//   htmlFor,
//   hint,
//   error,
//   children,
// }: {
//   label: string;
//   htmlFor?: string;
//   hint?: string;
//   error?: string;
//   children: ReactNode;
// }) {
//   return (
//     <div className="space-y-1.5">
//       <Label htmlFor={htmlFor}>{label}</Label>
//       {children}
//       {error ? (
//         <p className="text-xs text-red-600">{error}</p>
//       ) : hint ? (
//         <p className="text-xs text-slate-500">{hint}</p>
//       ) : null}
//     </div>
//   );
// }

// type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "outline";

// const badgeVariants: Record<BadgeVariant, string> = {
//   default: "bg-slate-100 text-slate-700",
//   success: "bg-emerald-100 text-emerald-700",
//   warning: "bg-amber-100 text-amber-800",
//   danger: "bg-red-100 text-red-700",
//   info: "bg-blue-100 text-blue-700",
//   outline: "border border-slate-200 text-slate-600",
// };

// export function Badge({
//   variant = "default",
//   className,
//   ...props
// }: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
//   return (
//     <span
//       className={cn(
//         "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
//         badgeVariants[variant],
//         className,
//       )}
//       {...props}
//     />
//   );
// }

// export function Alert({
//   variant = "info",
//   title,
//   children,
//   className,
// }: {
//   variant?: "info" | "error" | "success" | "warning";
//   title?: string;
//   children?: ReactNode;
//   className?: string;
// }) {
//   const styles = {
//     info: "border-blue-200 bg-blue-50 text-blue-800",
//     error: "border-red-200 bg-red-50 text-red-800",
//     success: "border-emerald-200 bg-emerald-50 text-emerald-800",
//     warning: "border-amber-200 bg-amber-50 text-amber-900",
//   }[variant];
//   return (
//     <div className={cn("flex gap-3 rounded-lg border p-3 text-sm", styles, className)} role="alert">
//       <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
//       <div>
//         {title ? <p className="font-medium">{title}</p> : null}
//         {children ? <div className={title ? "mt-1 opacity-90" : undefined}>{children}</div> : null}
//       </div>
//     </div>
//   );
// }

// export function Spinner({ className }: { className?: string }) {
//   return <Loader2 className={cn("h-5 w-5 animate-spin text-primary", className)} />;
// }

// export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
//   return (
//     <div className="flex min-h-[180px] flex-col items-center justify-center gap-3 text-sm text-slate-500">
//       <Spinner />
//       <p>{label}</p>
//     </div>
//   );
// }

// export function EmptyState({
//   title,
//   description,
//   action,
//   icon,
// }: {
//   title: string;
//   description?: string;
//   action?: ReactNode;
//   icon?: ReactNode;
// }) {
//   return (
//     <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed bg-slate-50/60 p-8 text-center">
//       <div className="rounded-full bg-white p-3 text-slate-400 shadow-sm">{icon ?? <Inbox className="h-6 w-6" />}</div>
//       <div>
//         <p className="font-medium text-slate-800">{title}</p>
//         {description ? <p className="mt-1 max-w-md text-sm text-slate-500">{description}</p> : null}
//       </div>
//       {action}
//     </div>
//   );
// }

// export function StatCard({
//   label,
//   value,
//   hint,
//   icon,
//   tone = "blue",
// }: {
//   label: string;
//   value: ReactNode;
//   hint?: string;
//   icon?: ReactNode;
//   tone?: "blue" | "emerald" | "amber" | "violet" | "slate";
// }) {
//   const tones = {
//     blue: "bg-blue-50 text-blue-600",
//     emerald: "bg-emerald-50 text-emerald-600",
//     amber: "bg-amber-50 text-amber-600",
//     violet: "bg-violet-50 text-violet-600",
//     slate: "bg-slate-100 text-slate-600",
//   }[tone];
//   return (
//     <Card>
//       <CardContent className="flex items-start justify-between gap-3 p-5">
//         <div>
//           <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
//           <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
//           {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
//         </div>
//         {icon ? <div className={cn("rounded-lg p-2.5", tones)}>{icon}</div> : null}
//       </CardContent>
//     </Card>
//   );
// }

// export function PageHeader({
//   title,
//   description,
//   actions,
// }: {
//   title: string;
//   description?: string;
//   actions?: ReactNode;
// }) {
//   return (
//     <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
//       <div>
//         <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
//         {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
//       </div>
//       {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
//     </div>
//   );
// }

// export function Modal({
//   open,
//   title,
//   description,
//   onClose,
//   children,
//   footer,
// }: {
//   open: boolean;
//   title: string;
//   description?: string;
//   onClose: () => void;
//   children: ReactNode;
//   footer?: ReactNode;
// }) {
//   if (!open) return null;
//   return (
//     <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
//       <div className="absolute inset-0 bg-slate-900/50" onClick={onClose} aria-hidden />
//       <div
//         role="dialog"
//         aria-modal="true"
//         aria-label={title}
//         className="relative z-10 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-xl"
//       >
//         <div className="flex items-start justify-between border-b px-5 py-4">
//           <div>
//             <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
//             {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
//           </div>
//           <button onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-slate-100" aria-label="Close dialog">
//             <X className="h-5 w-5" />
//           </button>
//         </div>
//         <div className="p-5">{children}</div>
//         {footer ? <div className="flex justify-end gap-2 border-t bg-slate-50 px-5 py-3">{footer}</div> : null}
//       </div>
//     </div>
//   );
// }

// export function Table({ children, className }: { children: ReactNode; className?: string }) {
//   return (
//     <div className="overflow-x-auto">
//       <table className={cn("w-full text-left text-sm", className)}>{children}</table>
//     </div>
//   );
// }

// export function Th({ className, ...props }: HTMLAttributes<HTMLTableCellElement>) {
//   return (
//     <th
//       className={cn(
//         "whitespace-nowrap border-b bg-slate-50 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500",
//         className,
//       )}
//       {...props}
//     />
//   );
// }

// export function Td({ className, ...props }: HTMLAttributes<HTMLTableCellElement>) {
//   return <td className={cn("border-b px-4 py-3 align-top text-slate-700", className)} {...props} />;
// }


import {
  forwardRef,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type LabelHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";

import { AlertCircle, Inbox, Loader2, X } from "lucide-react";

import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "destructive";
type ButtonSize = "sm" | "md" | "lg" | "icon";

const buttonVariants: Record<ButtonVariant, string> = {
  primary: "bg-primary text-primary-foreground hover:bg-blue-700 shadow-sm",
  secondary: "bg-secondary text-secondary-foreground hover:bg-slate-200",
  outline: "border border-input bg-white hover:bg-slate-50",
  ghost: "hover:bg-slate-100 text-slate-700",
  destructive: "bg-destructive text-destructive-foreground hover:bg-red-700 shadow-sm",
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  lg: "h-11 px-6 text-sm",
  icon: "h-9 w-9",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { className, variant = "primary", size = "md", loading, icon, children, disabled, ...props },
    ref,
  ) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-60",
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
      {...props}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  ),
);

Button.displayName = "Button";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl border bg-card text-card-foreground shadow-sm", className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex flex-col gap-1 border-b px-5 py-4", className)} {...props} />
  );
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-base font-semibold text-slate-900", className)} {...props} />
  );
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  ),
);

Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[96px] w-full rounded-md border border-input bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  ),
);

Textarea.displayName = "Textarea";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  ),
);

Select.displayName = "Select";

// FIXED: LabelHTMLAttributes supports the htmlFor property.
export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("text-sm font-medium text-slate-700", className)}
      {...props}
    />
  );
}

export function Field({
  label,
  htmlFor,
  hint,
  error,
  children,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {error ? (
        <p className="text-xs text-red-600">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
}

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "outline";

const badgeVariants: Record<BadgeVariant, string> = {
  default: "bg-slate-100 text-slate-700",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-red-100 text-red-700",
  info: "bg-blue-100 text-blue-700",
  outline: "border border-slate-200 text-slate-600",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        badgeVariants[variant],
        className,
      )}
      {...props}
    />
  );
}

export function Alert({
  variant = "info",
  title,
  children,
  className,
}: {
  variant?: "info" | "error" | "success" | "warning";
  title?: string;
  children?: ReactNode;
  className?: string;
}) {
  const styles = {
    info: "border-blue-200 bg-blue-50 text-blue-800",
    error: "border-red-200 bg-red-50 text-red-800",
    success: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warning: "border-amber-200 bg-amber-50 text-amber-900",
  }[variant];

  return (
    <div
      className={cn("flex gap-3 rounded-lg border p-3 text-sm", styles, className)}
      role="alert"
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        {title ? <p className="font-medium">{title}</p> : null}
        {children ? (
          <div className={title ? "mt-1 opacity-90" : undefined}>{children}</div>
        ) : null}
      </div>
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-5 w-5 animate-spin text-primary", className)} />;
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex min-h-[180px] flex-col items-center justify-center gap-3 text-sm text-slate-500">
      <Spinner />
      <p>{label}</p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed bg-slate-50/60 p-8 text-center">
      <div className="rounded-full bg-white p-3 text-slate-400 shadow-sm">
        {icon ?? <Inbox className="h-6 w-6" />}
      </div>
      <div>
        <p className="font-medium text-slate-800">{title}</p>
        {description ? (
          <p className="mt-1 max-w-md text-sm text-slate-500">{description}</p>
        ) : null}
      </div>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone = "blue",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: "blue" | "emerald" | "amber" | "violet" | "slate";
}) {
  const tones = {
    blue: "bg-blue-50 text-blue-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    violet: "bg-violet-50 text-violet-600",
    slate: "bg-slate-100 text-slate-600",
  }[tone];

  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 p-5">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
          {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
        </div>
        {icon ? <div className={cn("rounded-lg p-2.5", tones)}>{icon}</div> : null}
      </CardContent>
    </Card>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function Modal({
  open,
  title,
  description,
  onClose,
  children,
  footer,
}: {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/50"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative z-10 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-xl"
      >
        <div className="flex items-start justify-between border-b px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
            {description ? (
              <p className="mt-1 text-sm text-slate-500">{description}</p>
            ) : null}
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-5">{children}</div>
        {footer ? (
          <div className="flex justify-end gap-2 border-t bg-slate-50 px-5 py-3">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function Table({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className="overflow-x-auto">
      <table className={cn("w-full text-left text-sm", className)}>{children}</table>
    </div>
  );
}

export function Th({ className, ...props }: HTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        "whitespace-nowrap border-b bg-slate-50 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500",
        className,
      )}
      {...props}
    />
  );
}

export function Td({ className, ...props }: HTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={cn("border-b px-4 py-3 align-top text-slate-700", className)}
      {...props}
    />
  );
}