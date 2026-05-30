import { Braces } from "lucide-react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

type Tone = "neutral" | "positive" | "warning" | "danger";

const toneText: Record<Tone, string> = {
  neutral: "text-foreground",
  positive: "text-primary",
  warning: "text-warning",
  danger: "text-destructive",
};

const metricAccent: Record<Tone, string> = {
  neutral: "bg-slate-300",
  positive: "bg-green-500",
  warning: "bg-amber-500",
  danger: "bg-red-500",
};

const statusTone: Record<Tone, string> = {
  neutral: "border-border bg-background text-foreground",
  positive: "border-primary/25 bg-primary/10 text-primary",
  warning: "border-warning/30 bg-warning/15 text-foreground",
  danger: "border-destructive/30 bg-destructive/10 text-destructive",
};

type ButtonVariant = "primary" | "outline" | "danger" | "ghost";
type ButtonSize = "sm" | "default" | "lg" | "icon";

const buttonVariant: Record<ButtonVariant, string> = {
  primary: "bg-primary text-primary-foreground hover:bg-primary/90",
  outline: "border border-input bg-background text-foreground hover:bg-accent hover:text-accent-foreground",
  danger: "border border-destructive/40 bg-background text-destructive hover:bg-destructive/10",
  ghost: "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
};

const buttonSize: Record<ButtonSize, string> = {
  sm: "min-h-9 px-3 text-xs",
  default: "min-h-10 px-4 text-sm",
  lg: "min-h-12 px-4 text-sm",
  icon: "size-9 p-0",
};

const controlClass =
  "min-h-12 w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-5 text-foreground outline-none transition-[color,box-shadow,border-color] placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50";

export function Button({
  children,
  className,
  variant = "primary",
  size = "default",
  type = "button",
  ...props
}: ComponentPropsWithoutRef<"button"> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
}) {
  return (
    <button
      className={cx(
        "inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium leading-none transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 [&_svg]:shrink-0",
        buttonVariant[variant],
        buttonSize[size],
        className,
      )}
      type={type}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input({ className, ...props }: ComponentPropsWithoutRef<"input">) {
  return <input className={cx(controlClass, className)} {...props} />;
}

export function Select({ className, children, ...props }: ComponentPropsWithoutRef<"select">) {
  return (
    <select className={cx(controlClass, "appearance-auto", className)} {...props}>
      {children}
    </select>
  );
}

export function Textarea({ className, ...props }: ComponentPropsWithoutRef<"textarea">) {
  return <textarea className={cx(controlClass, "min-h-[128px] resize-y", className)} {...props} />;
}

export function CheckboxCard({
  children,
  className,
  inputClassName,
  ...props
}: ComponentPropsWithoutRef<"input"> & {
  children: ReactNode;
  inputClassName?: string;
}) {
  return (
    <label
      className={cx(
        "flex min-h-12 items-center gap-2 rounded-md border border-input bg-background px-3 text-sm font-medium text-foreground transition-colors hover:bg-accent",
        className,
      )}
    >
      <input
        className={cx("size-4 accent-primary", inputClassName)}
        type="checkbox"
        {...props}
      />
      <span className="min-w-0 break-words">{children}</span>
    </label>
  );
}

export function Table({
  className,
  ...props
}: ComponentPropsWithoutRef<"table">) {
  return (
    <div className="relative w-full overflow-x-auto rounded-lg border border-border bg-background">
      <table className={cx("w-full caption-bottom text-sm", className)} {...props} />
    </div>
  );
}

export function TableHeader({ className, ...props }: ComponentPropsWithoutRef<"thead">) {
  return <thead className={cx("bg-muted/55 [&_tr]:border-b", className)} {...props} />;
}

export function TableBody({ className, ...props }: ComponentPropsWithoutRef<"tbody">) {
  return <tbody className={cx("[&_tr:last-child]:border-0", className)} {...props} />;
}

export function TableRow({ className, ...props }: ComponentPropsWithoutRef<"tr">) {
  return (
    <tr
      className={cx("h-14 border-b border-border transition-colors hover:bg-muted/45", className)}
      {...props}
    />
  );
}

export function TableHead({ className, ...props }: ComponentPropsWithoutRef<"th">) {
  return (
    <th
      className={cx(
        "h-10 whitespace-nowrap px-3 text-left align-middle text-xs font-semibold uppercase leading-none tracking-wide text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}

export function TableCell({ className, ...props }: ComponentPropsWithoutRef<"td">) {
  return <td className={cx("px-3 py-3 align-middle text-sm", className)} {...props} />;
}

export function Eyebrow({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p
      className={cx(
        "mb-2 flex items-center gap-2 text-xs font-semibold uppercase leading-none tracking-wide text-muted-foreground",
        "before:block before:size-1.5 before:rounded-full before:bg-primary before:content-['']",
        className,
      )}
    >
      {children}
    </p>
  );
}

export function PageTitle({ children }: { children: ReactNode }) {
  return (
    <h1 className="m-0 text-3xl font-bold leading-tight tracking-tight md:text-4xl">
      {children}
    </h1>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  leading,
  trailing,
}: {
  eyebrow: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  leading?: ReactNode;
  trailing?: ReactNode;
}) {
  return (
    <header className="flex items-start justify-between gap-6 max-md:flex-col max-md:items-stretch">
      {leading}
      <div className="min-w-0 max-w-[820px]">
        <Eyebrow>{eyebrow}</Eyebrow>
        <PageTitle>{title}</PageTitle>
        {description ? <p className="m-0 mt-2 max-w-[680px] text-sm leading-6 text-muted-foreground md:text-base">{description}</p> : null}
      </div>
      {trailing}
    </header>
  );
}

export function BackLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <Link
      className="inline-flex min-h-10 items-center gap-2 rounded-md border border-primary bg-background px-4 text-sm font-medium text-primary transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      href={href}
    >
      {icon}
      {children}
    </Link>
  );
}

export function StatusPill({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex min-h-8 max-w-full items-center gap-2 rounded-md border px-3 text-xs font-medium leading-none [&_svg]:shrink-0",
        statusTone[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function StatusCluster({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-2 max-md:items-stretch">
      {children}
    </div>
  );
}

export function Notice({
  children,
  icon,
  tone = "neutral",
}: {
  children: ReactNode;
  icon?: ReactNode;
  tone?: Tone;
}) {
  return (
    <section
      className={cx(
        "flex items-start gap-2.5 rounded-lg border bg-card px-4 py-3 text-sm leading-6",
        tone === "positive" && "border-primary/25 bg-primary/10 text-primary",
        tone === "danger" && "border-destructive/30 bg-destructive/10 text-destructive",
        tone === "warning" && "border-warning/30 bg-warning/15 text-foreground",
        tone === "neutral" && "border-border text-foreground",
      )}
    >
      {icon}
      <span>{children}</span>
    </section>
  );
}

export function Panel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <article
      className={cx(
        "min-w-0 rounded-xl border border-border bg-card p-5 text-card-foreground shadow-sm md:p-6",
        className,
      )}
    >
      {children}
    </article>
  );
}

export function PanelHeader({
  eyebrow,
  title,
  icon,
}: {
  eyebrow: ReactNode;
  title: ReactNode;
  icon: ReactNode;
}) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <Eyebrow>{eyebrow}</Eyebrow>
        <h2 className="m-0 text-xl font-semibold leading-tight tracking-tight">{title}</h2>
      </div>
      <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary [&_svg]:size-[18px]">
        {icon}
      </span>
    </div>
  );
}

export function MetricCardGroup({
  children,
  className,
  ...props
}: {
  children: ReactNode;
  className?: string;
  columns?: 2 | 3 | 4;
} & Omit<ComponentPropsWithoutRef<"section">, "children" | "className">) {
  return (
    <section
      {...props}
      className={cx(
        "flex min-w-0 flex-col overflow-hidden rounded-xl border border-border bg-card text-card-foreground shadow-sm lg:flex-row lg:divide-x lg:divide-y-0 divide-y divide-border",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: Tone;
}) {
  return (
    <article className="relative grid min-h-[132px] flex-1 content-between gap-1 px-6 py-4 text-left">
      <div className={cx("absolute left-0 right-0 top-0 h-1", metricAccent[tone])} />
      <strong className={cx("break-words text-xl font-bold leading-tight", toneText[tone])}>{value}</strong>
      <span className="text-xs font-medium uppercase leading-5 tracking-wider text-muted-foreground">{label}</span>
      <small className="text-xs leading-5 text-muted-foreground/80">{detail}</small>
    </article>
  );
}

export function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-h-[40px] grid-cols-[minmax(112px,0.65fr)_minmax(0,1fr)] items-center gap-3 border-b border-border pb-3 max-md:grid-cols-1">
      <span className="text-xs font-medium leading-5 text-muted-foreground">{label}</span>
      <strong className="break-words text-right text-sm font-semibold leading-5 max-md:text-left">{value}</strong>
    </div>
  );
}

export function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-h-[68px] gap-1.5 rounded-lg border border-border bg-muted px-4 py-3">
      <span className="text-xs font-medium leading-5 text-muted-foreground">{label}</span>
      <strong className="break-words text-sm font-semibold leading-5">{value}</strong>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-muted p-4 text-sm leading-6 text-muted-foreground">
      {children}
    </div>
  );
}

export function ActionItem({
  tone,
  title,
  description,
}: {
  tone: Exclude<Tone, "neutral">;
  title: string;
  description: string;
}) {
  return (
    <article
      className={cx(
        "rounded-lg border p-4",
        tone === "positive" && "border-primary/25 bg-primary/10",
        tone === "warning" && "border-warning/30 bg-warning/15",
        tone === "danger" && "border-destructive/30 bg-destructive/10",
      )}
    >
      <strong className="block text-sm font-semibold leading-5 text-foreground">{title}</strong>
      <p className="m-0 mt-1 text-sm leading-6 text-muted-foreground">{description}</p>
    </article>
  );
}

export function JsonBlock({
  label,
  value,
}: {
  label: string;
  value: Record<string, unknown>;
}) {
  return (
    <section className="min-w-0 rounded-lg bg-[var(--primary-dark)] p-4 text-primary-foreground">
      <h3 className="mb-2.5 flex items-center gap-2 text-sm font-semibold tracking-normal text-primary-foreground/80">
        <Braces size={14} aria-hidden="true" />
        {label}
      </h3>
      <pre className="m-0 max-h-[260px] overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-relaxed">
        {JSON.stringify(value, null, 2)}
      </pre>
    </section>
  );
}

export function JsonDetails({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: ReactNode;
}) {
  return (
    <details className="rounded-lg bg-[var(--primary-dark)] px-3.5 py-3 text-primary-foreground">
      <summary className="flex cursor-pointer items-center gap-2 text-[13px] font-semibold text-primary-foreground/80">
        {icon}
        {label}
      </summary>
      <pre className="m-0 mt-3 max-h-[220px] overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-relaxed">
        {value}
      </pre>
    </details>
  );
}

export function PrimaryButton({ children, ...props }: ComponentPropsWithoutRef<"button">) {
  return (
    <Button size="lg" type="submit" {...props}>
      {children}
    </Button>
  );
}

export function IconTextButton({ children, ...props }: ComponentPropsWithoutRef<"button">) {
  return (
    <Button type="submit" variant="outline" {...props}>
      {children}
    </Button>
  );
}

export function FilterChip({
  href,
  active,
  children,
}: {
  href: string;
  active?: boolean;
  children: ReactNode;
}) {
  return (
    <Link
      className={cx(
        "inline-flex min-h-10 items-center gap-2 rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        active && "border-primary bg-primary text-primary-foreground hover:bg-primary/90",
      )}
      href={href}
    >
      {children}
    </Link>
  );
}

export function PagerLink({
  href,
  disabled,
  children,
}: {
  href: string;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <Link
      className={cx(
        "inline-flex min-h-10 items-center gap-2 rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        disabled && "pointer-events-none opacity-45",
      )}
      href={href}
    >
      {children}
    </Link>
  );
}

export function FieldGroup({
  label,
  children,
  wide,
}: {
  label: string;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <label className={cx("grid gap-[7px]", wide && "col-span-full")}>
      <span className="text-xs font-medium leading-5 text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

export function LabeledInput({
  label,
  type = "text",
  ...props
}: {
  label: string;
} & ComponentPropsWithoutRef<"input">) {
  return (
    <FieldGroup label={label}>
      <Input type={type} {...props} />
    </FieldGroup>
  );
}

export function LabeledTextarea({
  label,
  className,
  ...props
}: {
  label: string;
} & ComponentPropsWithoutRef<"textarea">) {
  return (
    <FieldGroup label={label} wide>
      <Textarea className={cx("font-mono text-xs leading-relaxed", className)} rows={5} {...props} />
    </FieldGroup>
  );
}

export function CompactList({ children }: { children: ReactNode }) {
  return <div className="grid gap-3">{children}</div>;
}

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  disabled?: boolean;
  title?: string;
};
