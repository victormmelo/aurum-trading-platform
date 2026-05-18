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
  positive: "text-primary",
  warning: "text-ink-muted-80",
  danger: "text-ink",
};

const statusTone: Record<Tone, string> = {
  neutral: "border-hairline text-ink",
  positive: "border-primary/35 bg-surface-pearl text-primary",
  warning: "border-hairline bg-surface-pearl text-ink-muted-80",
  danger: "border-hairline bg-canvas text-ink",
};

export function Eyebrow({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p
      className={cx(
        "mb-2 flex items-center gap-2 text-xs font-semibold uppercase leading-none tracking-[0.12px] text-ink-muted-48",
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
    <h1 className="m-0 font-display text-[34px] font-semibold leading-[1.08] tracking-[-0.28px] md:text-[48px]">
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
    <header className="flex items-start justify-between gap-8 border-b border-hairline pb-6 max-md:flex-col max-md:items-stretch">
      {leading}
      <div className="min-w-0 max-w-[820px]">
        <Eyebrow>{eyebrow}</Eyebrow>
        <PageTitle>{title}</PageTitle>
        {description ? <p className="m-0 mt-3 max-w-[680px] text-[17px] leading-[1.47] tracking-[-0.374px] text-ink-muted-48">{description}</p> : null}
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
      className="inline-flex min-h-[38px] items-center gap-2 rounded-full border border-primary bg-canvas px-4 text-sm font-normal text-primary transition-[background-color,transform] hover:bg-surface-pearl active:scale-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-focus"
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
        "inline-flex min-h-[34px] max-w-full items-center gap-2 rounded-full border bg-canvas px-3.5 text-sm font-normal leading-none tracking-[-0.224px] [&_svg]:shrink-0",
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
        "flex items-start gap-2.5 rounded-[18px] border bg-canvas px-4 py-3 text-sm leading-6 tracking-[-0.224px]",
        tone === "positive" && "border-primary/45 text-primary",
        tone === "danger" && "border-hairline text-ink",
        tone === "warning" && "border-hairline bg-surface-pearl text-ink-muted-80",
        tone === "neutral" && "border-hairline text-ink",
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
        "min-w-0 rounded-[18px] border border-hairline bg-canvas p-5 md:p-6",
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
        <h2 className="m-0 font-display text-[24px] font-semibold leading-[1.15] tracking-[-0.24px]">{title}</h2>
      </div>
      <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-full border border-hairline bg-canvas-parchment text-ink [&_svg]:size-[18px]">
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
    <article className="grid min-h-[132px] content-between gap-3 rounded-[18px] border border-hairline bg-canvas p-5">
      <span className="text-sm font-normal leading-[1.43] tracking-[-0.224px] text-ink-muted-48">{label}</span>
      <strong className={cx("break-words font-display text-[24px] font-semibold leading-[1.1] tracking-[-0.24px] md:text-[28px]", toneText[tone])}>
        {value}
      </strong>
      <small className="text-xs leading-[1.3] tracking-[-0.12px] text-ink-muted-48">{detail}</small>
    </article>
  );
}

export function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-h-[40px] grid-cols-[minmax(112px,0.65fr)_minmax(0,1fr)] items-center gap-3 border-b border-hairline pb-3 max-md:grid-cols-1">
      <span className="text-[13px] leading-[1.43] tracking-[-0.224px] text-ink-muted-48">{label}</span>
      <strong className="break-words text-right text-[17px] font-semibold leading-[1.24] tracking-[-0.374px] max-md:text-left">{value}</strong>
    </div>
  );
}

export function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-h-[68px] gap-1.5 rounded-[18px] border border-hairline bg-surface-pearl px-4 py-3">
      <span className="text-[13px] leading-[1.43] tracking-[-0.224px] text-ink-muted-48">{label}</span>
      <strong className="break-words text-[17px] font-semibold leading-[1.24] tracking-[-0.374px]">{value}</strong>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-[18px] border border-dashed border-hairline bg-canvas-parchment p-4 text-sm leading-6 tracking-[-0.224px] text-ink-muted-48">
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
    <section className="min-w-0 rounded-[18px] bg-ink p-4 text-on-primary">
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
    <details className="rounded-[18px] bg-ink px-3.5 py-3 text-on-primary">
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
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full bg-primary px-[22px] text-[17px] font-normal leading-none tracking-[-0.374px] text-on-primary transition-[background-color,transform] hover:bg-primary-focus active:scale-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-focus"
      type="submit"
    >
      {children}
    </button>
  );
}

export function IconTextButton({ children }: { children: ReactNode }) {
  return (
    <button
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full border border-primary bg-canvas px-[18px] text-[17px] font-normal leading-none tracking-[-0.374px] text-primary transition-[background-color,transform] hover:bg-surface-pearl active:scale-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-focus"
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
        "inline-flex min-h-[38px] items-center gap-2 rounded-full border border-hairline bg-canvas px-4 text-sm font-normal tracking-[-0.224px] text-primary transition-[background-color,transform] hover:bg-surface-pearl active:scale-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-focus",
        active && "border-primary bg-primary text-on-primary hover:bg-primary",
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
        "inline-flex min-h-[38px] items-center gap-2 rounded-full border border-primary bg-canvas px-4 text-sm font-normal tracking-[-0.224px] text-primary transition-[background-color,transform] hover:bg-surface-pearl active:scale-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-focus",
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
      <span className="text-[13px] leading-[1.43] tracking-[-0.224px] text-ink-muted-48">{label}</span>
      {children}
    </label>
  );
}

const fieldClass =
  "min-h-11 w-full rounded-full border border-hairline bg-canvas px-4 py-2.5 text-[17px] leading-[1.47] tracking-[-0.374px] text-ink outline-none transition-colors focus:border-primary-focus focus:ring-2 focus:ring-primary-focus/15";

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
        className={cx(fieldClass, "min-h-[128px] resize-y rounded-[18px] font-mono text-xs leading-relaxed")}
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
