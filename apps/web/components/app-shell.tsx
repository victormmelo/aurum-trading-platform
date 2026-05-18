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
    <main className="min-h-screen bg-parchment text-ink lg:grid lg:grid-cols-[232px_minmax(0,1fr)]">
      <aside className="border-r border-line bg-parchment/90 px-4 py-4 backdrop-blur max-lg:border-b">
        <div className="grid gap-5 lg:sticky lg:top-4">
          <AurumBrand />
          <nav
            className="grid gap-1 max-lg:grid-cols-4 max-md:grid-cols-2"
            aria-label="Navegação principal"
          >
            {navItems.map(({ label, href, icon: Icon, disabled, title }) => (
              <Link
                aria-disabled={disabled ? "true" : undefined}
                className={cx(
                  "flex min-h-11 items-center gap-3 rounded-[11px] border border-transparent px-3.5 text-sm font-normal tracking-[-0.224px] text-muted transition-colors",
                  label === activeLabel && "border-line bg-canvas text-ink",
                  disabled && "pointer-events-none opacity-45",
                  !disabled && label !== activeLabel && "hover:bg-canvas/70 hover:text-ink",
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
      <section className="mx-auto flex min-w-0 w-full max-w-[1600px] flex-col gap-6 px-6 py-6 max-md:p-4">
        {children}
      </section>
    </main>
  );
}

function AurumBrand() {
  return (
    <div className="flex min-h-[56px] items-center gap-3 border-b border-line pb-4">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-ink text-[17px] font-semibold text-canvas">
        A
      </div>
      <div>
        <strong className="block text-[17px] font-semibold leading-tight tracking-[-0.34px]">Aurum</strong>
        <span className="mt-0.5 block text-xs leading-none tracking-[-0.12px] text-muted">BTC Testnet</span>
      </div>
    </div>
  );
}
