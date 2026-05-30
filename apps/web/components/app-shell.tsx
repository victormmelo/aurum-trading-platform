import Link from "next/link";
import type { ReactNode } from "react";
import { Bell, Search } from "lucide-react";

import { Button, cx, type NavItem } from "@/components/ui";

export function AppShell({
  navItems,
  activeLabel,
  topbarActions,
  children,
}: {
  navItems: readonly NavItem[];
  activeLabel: string;
  topbarActions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[var(--dashboard-background)] text-foreground">
      <header className="fixed inset-x-0 top-0 z-50 flex h-[var(--dashboard-topbar-height)] items-center gap-3 border-b border-border bg-background px-3 shadow-sm md:px-6">
        <Link href="/" className="flex min-w-0 shrink-0 items-center gap-3" aria-label="Aurum dashboard">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary text-sm font-semibold text-primary-foreground">
            A
          </div>
          <div className="hidden min-w-0 sm:block">
            <strong className="block truncate text-sm font-semibold leading-none">Aurum Trading</strong>
            <span className="mt-1 block truncate text-xs leading-none text-muted-foreground">BTCUSDT Testnet</span>
          </div>
        </Link>

        <div className="h-6 w-px shrink-0 bg-border" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-muted-foreground">{activeLabel}</p>
        </div>
        <div className="ml-auto flex min-w-0 shrink-0 items-center gap-2">
          {topbarActions ? (
            <div className="flex min-w-0 items-center gap-2">
              {topbarActions}
            </div>
          ) : null}
          <Button
            className="hidden md:inline-flex"
            size="sm"
            type="button"
            variant="ghost"
          >
            <Search size={16} aria-hidden="true" />
            <span>Buscar</span>
            <kbd className="rounded border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">Ctrl K</kbd>
          </Button>
          <Button
            aria-label="Notificações"
            size="icon"
            type="button"
            variant="ghost"
          >
            <Bell size={17} aria-hidden="true" />
          </Button>
        </div>
      </header>

      <main className="min-h-screen pt-[var(--dashboard-topbar-height)] lg:grid lg:grid-cols-[18rem_minmax(0,1fr)]">
        <aside className="border-r border-sidebar-border bg-sidebar text-sidebar-foreground max-lg:border-b lg:sticky lg:top-[var(--dashboard-topbar-height)] lg:h-[calc(100vh-var(--dashboard-topbar-height))]">
          <div className="grid gap-4 px-3 py-3 lg:h-full lg:grid-rows-[minmax(0,1fr)_auto]">
            <nav
              className="grid gap-1 overflow-y-auto max-lg:grid-cols-4 max-md:grid-cols-2"
              aria-label="Navegação principal"
            >
              {navItems.map(({ label, href, icon: Icon, disabled, title }) => (
                <Link
                  aria-disabled={disabled ? "true" : undefined}
                  className={cx(
                    "flex min-h-10 items-center gap-3 rounded-md border border-transparent px-3 text-sm font-medium text-sidebar-foreground/85 transition-colors",
                    label === activeLabel && "border-sidebar-border bg-sidebar-accent text-sidebar-accent-foreground",
                    disabled && "pointer-events-none opacity-45",
                    !disabled && label !== activeLabel && "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
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
            <div className="hidden rounded-md border border-sidebar-border bg-white/10 px-3 py-2 text-xs leading-5 text-sidebar-foreground/80 lg:block">
              MVP restrito a Binance Spot Testnet, BTCUSDT, long-only e sem alavancagem.
            </div>
          </div>
        </aside>
        <section className="mx-auto flex min-w-0 w-full max-w-[1600px] flex-col gap-6 px-4 py-4 md:px-6 md:py-6">
          {children}
        </section>
      </main>
    </div>
  );
}
