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
  warning: "text-signal",
  danger: "text-danger",
};

const statusTone: Record<Tone, string> = {
  neutral: "border-ink/20 text-ink",
  positive: "border-success/35 bg-success/5 text-success",
  warning: "border-signal/35 bg-signal/5 text-signal",
  danger: "border-danger/35 bg-danger/5 text-danger",
};

export function Eyebrow({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p
      className={cx(
        "mb-2 flex items-center gap-2 text-xs font-bold uppercase leading-none tracking-[0.56px] text-muted",
        "before:block before:size-1.5 before:rounded-full before:bg-signal before:content-['']",
        className,
      )}
    >
      {children}
    </p>
  );
}

export function PageTitle({ children }: { children: ReactNode }) {
  return (
    <h1 className="m-0 text-[clamp(32px,4vw,54px)] font-medium leading-[0.98] tracking-[-0.02em]">
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
        {description ? <p className="m-0 mt-3 max-w-[680px] text-sm leading-6 text-muted">{description}</p> : null}
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
      className="inline-flex min-h-[38px] items-center gap-2 rounded-full border-[1.5px] border-ink bg-aurum-white px-4 text-sm font-medium text-ink transition-colors hover:bg-ink hover:text-canvas"
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
        "inline-flex min-h-[34px] max-w-full items-center gap-2 rounded-full border-[1.5px] bg-aurum-white px-3.5 text-sm font-medium leading-none [&_svg]:shrink-0",
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
        "flex items-start gap-2.5 rounded-[24px] border bg-surface px-4 py-3 text-sm leading-6",
        tone === "positive" && "border-success/45 text-success",
        tone === "danger" && "border-danger/45 text-danger",
        tone === "warning" && "border-signal/45 text-signal",
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
        "min-w-0 rounded-[32px] border border-ink/10 bg-surface p-5 shadow-[0_18px_42px_rgba(20,20,19,0.055)]",
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
        <h2 className="m-0 text-[22px] font-medium leading-tight tracking-[-0.02em]">{title}</h2>
      </div>
      <span className="inline-flex size-[38px] shrink-0 items-center justify-center rounded-full border border-ink/20 bg-aurum-white text-ink [&_svg]:size-[18px]">
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
    <article className="grid min-h-[126px] content-between gap-3 rounded-[28px] border border-ink/10 bg-surface p-5 shadow-[0_14px_32px_rgba(20,20,19,0.045)]">
      <span className="text-[13px] font-medium text-muted">{label}</span>
      <strong className={cx("break-words text-[clamp(22px,1.9vw,28px)] font-medium leading-[1.05]", toneText[tone])}>
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
    <div className="grid min-h-[68px] gap-1.5 rounded-[22px] border border-line bg-aurum-white px-4 py-3">
      <span className="text-[13px] text-muted">{label}</span>
      <strong className="break-words text-base font-medium leading-snug">{value}</strong>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-[22px] border border-dashed border-line bg-canvas/70 p-4 text-sm leading-6 text-muted">
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
    <section className="min-w-0 rounded-[24px] bg-ink p-4 text-canvas">
      <h3 className="mb-2.5 flex items-center gap-2 text-sm font-bold tracking-normal text-signal-light">
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
    <details className="rounded-[24px] bg-ink px-3.5 py-3 text-canvas">
      <summary className="flex cursor-pointer items-center gap-2 text-[13px] font-bold text-signal-light">
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
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full border-[1.5px] border-ink bg-ink px-[18px] font-medium text-canvas transition-transform active:translate-y-px"
      type="submit"
    >
      {children}
    </button>
  );
}

export function IconTextButton({ children }: { children: ReactNode }) {
  return (
    <button
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full border-[1.5px] border-ink bg-aurum-white px-[18px] font-medium text-ink transition-colors hover:bg-ink hover:text-canvas"
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
        "inline-flex min-h-[38px] items-center gap-2 rounded-full border-[1.5px] border-ink bg-aurum-white px-4 text-sm font-medium text-ink transition-colors hover:bg-ink hover:text-canvas",
        active && "bg-ink text-canvas",
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
        "inline-flex min-h-[38px] items-center gap-2 rounded-full border-[1.5px] border-ink bg-aurum-white px-4 text-sm font-medium text-ink transition-colors hover:bg-ink hover:text-canvas",
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
  "min-h-11 w-full rounded-[20px] border-[1.5px] border-line bg-aurum-white px-3.5 py-2.5 text-ink outline-none transition-colors focus:border-signal";

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
