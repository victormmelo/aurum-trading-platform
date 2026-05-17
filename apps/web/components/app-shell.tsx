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
    <main className="grid min-h-screen grid-cols-[280px_minmax(0,1fr)] max-lg:grid-cols-1">
      <aside className="flex flex-col gap-8 bg-ink px-[18px] py-6 text-canvas max-lg:p-4">
        <AurumBrand />
        <nav
          className="grid gap-1 rounded-[32px] border border-aurum-white/10 bg-aurum-white/10 p-2 max-lg:grid-cols-4 max-md:grid-cols-1"
          aria-label="Navegação principal"
        >
          {navItems.map(({ label, href, icon: Icon, disabled, title }) => (
            <Link
              aria-disabled={disabled ? "true" : undefined}
              className={cx(
                "flex min-h-[42px] items-center gap-2.5 rounded-full px-3.5 text-[15px] font-medium text-canvas",
                label === activeLabel && "bg-aurum-white text-ink",
                disabled && "opacity-45",
                !disabled && "hover:bg-aurum-white hover:text-ink",
              )}
              href={href}
              key={label}
              title={title}
            >
              <Icon size={18} aria-hidden />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
      </aside>
      <section className="flex min-w-0 flex-col gap-6 p-6 max-md:p-4">{children}</section>
    </main>
  );
}

function AurumBrand() {
  return (
    <div className="flex min-h-[52px] items-center gap-3">
      <div className="grid h-11 w-16 grid-cols-2">
        <span className="block size-11 rounded-full bg-mastercard-red" />
        <span className="-ml-6 block size-11 rounded-full bg-mastercard-yellow opacity-90" />
      </div>
      <div>
        <strong className="block text-lg font-bold tracking-[-0.36px]">Aurum</strong>
        <span className="mt-0.5 block text-[13px] text-line">BTC Testnet</span>
      </div>
    </div>
  );
}
