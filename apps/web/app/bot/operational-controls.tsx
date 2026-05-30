"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { CirclePlay, OctagonAlert, Pause, X } from "lucide-react";

import {
  emergencyStopBot,
  initializeBot,
  pauseBot,
  resumeBot,
} from "@/app/bot/actions";
import { cx } from "@/components/ui";
import type { BotStatus } from "@/lib/api";

export function OperationalControls({ bot }: { bot: BotStatus | null }) {
  const [stopOpen, setStopOpen] = useState(false);
  const [confirmation, setConfirmation] = useState("");
  const stopDisabled = !bot || bot.status === "emergency_stop";

  return (
    <>
      <div className="hidden min-w-0 items-center gap-2 lg:flex">
        <StatusDot status={bot?.status} />
        {!bot ? (
          <form action={initializeBot}>
            <TopbarPrimaryButton>
              <CirclePlay size={15} aria-hidden="true" />
              Inicializar
            </TopbarPrimaryButton>
          </form>
        ) : null}
        {bot?.status === "paused" ? (
          <form action={resumeBot}>
            <TopbarPrimaryButton>
              <CirclePlay size={15} aria-hidden="true" />
              Retomar
            </TopbarPrimaryButton>
          </form>
        ) : null}
        {bot?.status === "running" ? (
          <form action={pauseBot}>
            <TopbarSecondaryButton>
              <Pause size={15} aria-hidden="true" />
              Pausar
            </TopbarSecondaryButton>
          </form>
        ) : null}
        {bot ? (
          <button
            className={cx(
              "inline-flex h-9 items-center justify-center gap-2 rounded-md border border-destructive/35 bg-background px-3 text-sm font-medium leading-none text-destructive transition-colors hover:bg-destructive/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              stopDisabled && "cursor-not-allowed opacity-50",
            )}
            disabled={stopDisabled}
            onClick={() => setStopOpen(true)}
            type="button"
          >
            <OctagonAlert size={15} aria-hidden="true" />
            Acionar parada
          </button>
        ) : null}
      </div>

      <div className="flex min-w-0 items-center gap-2 lg:hidden">
        <StatusDot status={bot?.status} compact />
        {bot?.status === "paused" ? (
          <form action={resumeBot}>
            <MobileActionButton label="Retomar robô">
              <CirclePlay size={16} aria-hidden="true" />
            </MobileActionButton>
          </form>
        ) : null}
        {bot?.status === "running" ? (
          <form action={pauseBot}>
            <MobileActionButton label="Pausar robô">
              <Pause size={16} aria-hidden="true" />
            </MobileActionButton>
          </form>
        ) : null}
        {bot ? (
          <button
            aria-label="Acionar parada"
            className={cx(
              "inline-flex size-9 items-center justify-center rounded-md border border-destructive/35 bg-background text-destructive transition-colors hover:bg-destructive/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              stopDisabled && "cursor-not-allowed opacity-50",
            )}
            disabled={stopDisabled}
            onClick={() => setStopOpen(true)}
            type="button"
          >
            <OctagonAlert size={16} aria-hidden="true" />
          </button>
        ) : (
          <form action={initializeBot}>
            <button
              aria-label="Inicializar robô"
              className="inline-flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              type="submit"
            >
              <CirclePlay size={16} aria-hidden="true" />
            </button>
          </form>
        )}
      </div>

      {stopOpen ? (
        <div
          aria-labelledby="emergency-stop-title"
          aria-modal="true"
          className="fixed inset-0 z-[80] grid place-items-center bg-foreground/35 px-4 py-6"
          role="dialog"
        >
          <form
            action={emergencyStopBot}
            className="w-full max-w-[420px] rounded-xl border border-border bg-card p-5 text-card-foreground shadow-xl"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="m-0 text-xs font-semibold uppercase leading-none text-destructive">Parada de emergência</p>
                <h2 id="emergency-stop-title" className="m-0 mt-2 text-lg font-semibold leading-6">
                  Confirmar bloqueio operacional
                </h2>
              </div>
              <button
                aria-label="Fechar modal"
                className="inline-flex size-9 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                onClick={() => setStopOpen(false)}
                type="button"
              >
                <X size={17} aria-hidden="true" />
              </button>
            </div>
            <p className="m-0 mt-3 text-sm leading-6 text-muted-foreground">
              Esta ação interrompe novas operações e bloqueia retomada automática. Digite PARAR para confirmar.
            </p>
            <label className="mt-4 grid gap-2">
              <span className="text-xs font-medium leading-5 text-muted-foreground">Confirmação</span>
              <input
                autoFocus
                className="min-h-12 w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-5 text-foreground outline-none transition-colors placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                name="confirmation"
                onChange={(event) => setConfirmation(event.target.value)}
                placeholder="PARAR"
                value={confirmation}
              />
            </label>
            <input name="reason" type="hidden" value="Parada de emergência acionada pelo dashboard" />
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button
                className="inline-flex min-h-10 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium leading-none text-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                onClick={() => setStopOpen(false)}
                type="button"
              >
                Cancelar
              </button>
              <button
                className={cx(
                  "inline-flex min-h-10 items-center justify-center gap-2 rounded-md bg-destructive px-4 text-sm font-medium leading-none text-destructive-foreground transition-colors hover:bg-destructive/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  confirmation.trim().toUpperCase() !== "PARAR" && "cursor-not-allowed opacity-50",
                )}
                disabled={confirmation.trim().toUpperCase() !== "PARAR"}
                type="submit"
              >
                <OctagonAlert size={16} aria-hidden="true" />
                Confirmar parada
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </>
  );
}

function StatusDot({ status, compact = false }: { status: string | undefined; compact?: boolean }) {
  return (
    <span className="inline-flex min-w-0 items-center gap-2 rounded-md border border-border bg-background px-2.5 py-2 text-xs font-medium leading-none text-foreground">
      <span className={cx("size-2 rounded-full", statusDotClass(status))} aria-hidden="true" />
      <span className={cx("truncate", compact && "sr-only")}>{statusLabel(status)}</span>
    </span>
  );
}

function TopbarPrimaryButton({ children }: { children: ReactNode }) {
  return (
    <button
      className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-primary px-3 text-sm font-medium leading-none text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      type="submit"
    >
      {children}
    </button>
  );
}

function TopbarSecondaryButton({ children }: { children: ReactNode }) {
  return (
    <button
      className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-input bg-background px-3 text-sm font-medium leading-none text-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      type="submit"
    >
      {children}
    </button>
  );
}

function MobileActionButton({ label, children }: { label: string; children: ReactNode }) {
  return (
    <button
      aria-label={label}
      className="inline-flex size-9 items-center justify-center rounded-md border border-input bg-background text-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      type="submit"
    >
      {children}
    </button>
  );
}

function statusLabel(value: string | undefined) {
  if (value === "running") return "Rodando";
  if (value === "paused") return "Pausado";
  if (value === "emergency_stop") return "Parada";
  return "Não inicializado";
}

function statusDotClass(value: string | undefined) {
  if (value === "running") return "bg-primary";
  if (value === "paused") return "bg-warning";
  if (value === "emergency_stop") return "bg-destructive";
  return "bg-muted-foreground";
}
