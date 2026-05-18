import Link from "next/link";
import type { ReactNode } from "react";

import { cx, type NavItem } from "@/components/ui";

export function AppShell({
  navItems,
  activeLabel,
  children,
}: {
  navItems: readonly NavItem[];
  activeLabel: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-canvas text-ink lg:grid lg:grid-cols-[264px_minmax(0,1fr)]">
      <aside className="border-r border-ink/10 bg-canvas px-4 py-5 max-lg:border-b max-lg:py-4">
        <div className="grid gap-5 lg:sticky lg:top-5">
          <AurumBrand />
          <nav
            className="grid gap-1.5 rounded-[28px] border border-ink/10 bg-surface p-1.5 shadow-[0_16px_38px_rgba(20,20,19,0.055)] max-lg:grid-cols-4 max-md:grid-cols-2"
            aria-label="Navegação principal"
          >
            {navItems.map(({ label, href, icon: Icon, disabled, title }) => (
              <Link
                aria-disabled={disabled ? "true" : undefined}
                className={cx(
                  "flex min-h-11 items-center gap-3 rounded-[22px] px-3.5 text-sm font-medium text-muted transition-colors",
                  label === activeLabel && "bg-ink text-canvas shadow-[0_8px_18px_rgba(20,20,19,0.14)]",
                  disabled && "pointer-events-none opacity-45",
                  !disabled && label !== activeLabel && "hover:bg-canvas hover:text-ink",
                )}
                href={href}
                key={label}
                title={title}
              >
                <Icon size={17} aria-hidden className="shrink-0" />
                <span className="truncate">{label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </aside>
      <section className="mx-auto flex min-w-0 w-full max-w-[1680px] flex-col gap-5 px-6 py-5 max-md:p-4">
        {children}
      </section>
    </main>
  );
}

function AurumBrand() {
  return (
    <div className="flex min-h-[58px] items-center gap-3 rounded-[28px] bg-ink px-3.5 py-3 text-canvas shadow-[0_18px_42px_rgba(20,20,19,0.16)]">
      <div className="grid h-9 w-14 shrink-0 grid-cols-2">
        <span className="block size-9 rounded-full bg-mastercard-red" />
        <span className="-ml-5 block size-9 rounded-full bg-mastercard-yellow opacity-90" />
      </div>
      <div>
        <strong className="block text-[17px] font-bold leading-tight tracking-[-0.34px]">Aurum</strong>
        <span className="mt-0.5 block text-xs text-canvas/70">BTC Testnet</span>
      </div>
    </div>
  );
}
