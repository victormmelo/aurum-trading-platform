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
    <main className="min-h-screen bg-parchment text-ink lg:grid lg:grid-cols-[256px_minmax(0,1fr)]">
      <aside className="border-r border-line bg-canvas/90 px-4 py-4 max-lg:border-b">
        <div className="grid gap-4 lg:sticky lg:top-4">
          <AurumBrand />
          <nav
            className="grid gap-1 rounded-[18px] border border-line bg-surface p-1 max-lg:grid-cols-4 max-md:grid-cols-2"
            aria-label="Navegação principal"
          >
            {navItems.map(({ label, href, icon: Icon, disabled, title }) => (
              <Link
                aria-disabled={disabled ? "true" : undefined}
                className={cx(
                  "flex min-h-11 items-center gap-3 rounded-[14px] px-3.5 text-sm font-medium text-muted transition-colors",
                  label === activeLabel && "bg-ink text-canvas",
                  disabled && "pointer-events-none opacity-45",
                  !disabled && label !== activeLabel && "hover:bg-parchment hover:text-ink",
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
    <div className="flex min-h-[56px] items-center gap-3 rounded-[18px] border border-line bg-canvas px-3.5 py-3">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-ink text-[17px] font-semibold text-canvas">
        A
      </div>
      <div>
        <strong className="block text-[17px] font-semibold leading-tight tracking-[-0.34px]">Aurum</strong>
        <span className="mt-0.5 block text-xs text-muted">BTC Testnet</span>
      </div>
    </div>
  );
}
