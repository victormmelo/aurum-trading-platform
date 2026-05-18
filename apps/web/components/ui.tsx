import { Braces } from "lucide-react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

type Tone = "neutral" | "positive" | "warning" | "danger";

const toneText: Record<Tone, string> = {
  neutral: "text-ink",
  positive: "text-success",
  warning: "text-warning",
  danger: "text-danger",
};

const statusTone: Record<Tone, string> = {
  neutral: "border-line text-ink",
  positive: "border-success/35 bg-success/5 text-success",
  warning: "border-warning/35 bg-warning/5 text-warning",
  danger: "border-danger/35 bg-danger/5 text-danger",
};

export function Eyebrow({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p
      className={cx(
        "mb-2 flex items-center gap-2 text-xs font-semibold uppercase leading-none tracking-[0.24px] text-muted",
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
    <h1 className="m-0 font-display text-[clamp(32px,4vw,54px)] font-semibold leading-[1.05] tracking-[-0.02em]">
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
        {description ? <p className="m-0 mt-3 max-w-[680px] text-[15px] leading-6 text-muted">{description}</p> : null}
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
      className="inline-flex min-h-[38px] items-center gap-2 rounded-full border border-line bg-canvas px-4 text-sm font-medium text-primary transition-colors hover:bg-parchment"
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
        "inline-flex min-h-[34px] max-w-full items-center gap-2 rounded-full border bg-canvas px-3.5 text-sm font-medium leading-none [&_svg]:shrink-0",
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
        "flex items-start gap-2.5 rounded-[18px] border bg-canvas px-4 py-3 text-sm leading-6",
        tone === "positive" && "border-success/45 text-success",
        tone === "danger" && "border-danger/45 text-danger",
        tone === "warning" && "border-warning/45 text-warning",
        tone === "neutral" && "border-line text-ink",
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
        "min-w-0 rounded-[18px] border border-line bg-canvas p-5",
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
    <div className="mb-4 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <Eyebrow>{eyebrow}</Eyebrow>
        <h2 className="m-0 font-display text-[22px] font-semibold leading-tight tracking-[-0.02em]">{title}</h2>
      </div>
      <span className="inline-flex size-[38px] shrink-0 items-center justify-center rounded-full border border-line bg-parchment text-ink [&_svg]:size-[18px]">
        {icon}
      </span>
    </div>
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
  tone: Exclude<Tone, "danger">;
}) {
  return (
    <article className="grid min-h-[126px] content-between gap-3 rounded-[18px] border border-line bg-canvas p-5">
      <span className="text-[13px] font-medium text-muted">{label}</span>
      <strong className={cx("break-words font-display text-[clamp(22px,1.9vw,28px)] font-semibold leading-[1.08] tracking-[-0.02em]", toneText[tone])}>
        {value}
      </strong>
      <small className="text-xs leading-snug text-muted">{detail}</small>
    </article>
  );
}

export function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-h-[40px] grid-cols-[minmax(112px,0.65fr)_minmax(0,1fr)] items-center gap-3 border-b border-line pb-3 max-md:grid-cols-1">
      <span className="text-[13px] text-muted">{label}</span>
      <strong className="break-words text-right text-base font-medium leading-snug max-md:text-left">{value}</strong>
    </div>
  );
}

export function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-h-[68px] gap-1.5 rounded-[18px] border border-line bg-canvas px-4 py-3">
      <span className="text-[13px] text-muted">{label}</span>
      <strong className="break-words text-base font-medium leading-snug">{value}</strong>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-[18px] border border-dashed border-line bg-parchment p-4 text-sm leading-6 text-muted">
      {children}
    </div>
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
    <section className="min-w-0 rounded-[18px] bg-ink p-4 text-canvas">
      <h3 className="mb-2.5 flex items-center gap-2 text-sm font-semibold tracking-normal text-primary-on-dark">
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
    <details className="rounded-[18px] bg-ink px-3.5 py-3 text-canvas">
      <summary className="flex cursor-pointer items-center gap-2 text-[13px] font-semibold text-primary-on-dark">
        {icon}
        {label}
      </summary>
      <pre className="m-0 mt-3 max-h-[220px] overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-relaxed">
        {value}
      </pre>
    </details>
  );
}

export function PrimaryButton({ children }: { children: ReactNode }) {
  return (
    <button
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full bg-primary px-[22px] font-medium text-canvas transition-colors hover:bg-primary-focus active:scale-[0.99]"
      type="submit"
    >
      {children}
    </button>
  );
}

export function IconTextButton({ children }: { children: ReactNode }) {
  return (
    <button
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full border border-line bg-canvas px-[18px] font-medium text-primary transition-colors hover:bg-parchment"
      type="submit"
    >
      {children}
    </button>
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
        "inline-flex min-h-[38px] items-center gap-2 rounded-full border border-line bg-canvas px-4 text-sm font-medium text-primary transition-colors hover:bg-parchment",
        active && "border-primary bg-primary text-canvas hover:bg-primary",
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
        "inline-flex min-h-[38px] items-center gap-2 rounded-full border border-line bg-canvas px-4 text-sm font-medium text-primary transition-colors hover:bg-parchment",
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
      <span className="text-[13px] text-muted">{label}</span>
      {children}
    </label>
  );
}

const fieldClass =
  "min-h-11 w-full rounded-[14px] border border-line bg-canvas px-3.5 py-2.5 text-ink outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/15";

export function LabeledInput({
  label,
  name,
  type = "text",
  defaultValue,
  placeholder,
  min,
  required,
}: {
  label: string;
  name: string;
  type?: string;
  defaultValue?: string;
  placeholder?: string;
  min?: string;
  required?: boolean;
}) {
  return (
    <FieldGroup label={label}>
      <input
        className={fieldClass}
        name={name}
        type={type}
        defaultValue={defaultValue}
        placeholder={placeholder}
        min={min}
        required={required}
      />
    </FieldGroup>
  );
}

export function LabeledTextarea({
  label,
  name,
  placeholder,
}: {
  label: string;
  name: string;
  placeholder: string;
}) {
  return (
    <FieldGroup label={label} wide>
      <textarea
        className={cx(fieldClass, "min-h-[128px] resize-y font-mono text-xs leading-relaxed")}
        name={name}
        placeholder={placeholder}
        rows={5}
      />
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
