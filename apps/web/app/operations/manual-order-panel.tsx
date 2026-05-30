"use client";

import { useState } from "react";
import { Send } from "lucide-react";

import { submitManualOrder } from "@/app/operations/actions";
import { FieldGroup, LabeledInput, Notice, Panel, PanelHeader, PrimaryButton, cx } from "@/components/ui";

type ManualSide = "BUY" | "SELL";

export function ManualOrderPanel() {
  const [side, setSide] = useState<ManualSide>("BUY");

  return (
    <Panel>
      <PanelHeader eyebrow="Intervenção manual" title="Ordem protegida" icon={<Send />} />
      <Notice tone="warning">
        Use intervenção manual apenas para validação controlada em Testnet. O MVP não executa Mainnet, alavancagem ou short.
      </Notice>
      <form action={submitManualOrder} className="mt-5 grid gap-4">
        <FieldGroup label="Ação operacional">
          <div className="grid grid-cols-2 gap-2 rounded-lg border border-border bg-muted p-1">
            <button
              className={sideButtonClass(side === "BUY")}
              type="button"
              onClick={() => setSide("BUY")}
            >
              Comprar por USDT
            </button>
            <button
              className={sideButtonClass(side === "SELL")}
              type="button"
              onClick={() => setSide("SELL")}
            >
              Vender BTC
            </button>
          </div>
        </FieldGroup>
        <input name="side" type="hidden" value={side} />

        {side === "BUY" ? (
          <LabeledInput
            label="Valor da compra"
            name="quote_quantity"
            type="number"
            min="0"
            step="0.00000001"
            placeholder="25 USDT"
            required
          />
        ) : (
          <LabeledInput
            label="Quantidade para venda"
            name="quantity"
            type="number"
            min="0"
            step="0.00000001"
            placeholder="0.00025 BTC"
            required
          />
        )}

        <p className="m-0 text-xs leading-5 text-muted-foreground">
          {side === "BUY"
            ? "Compras usam saldo USDT disponível na Binance Spot Testnet."
            : "Vendas long-only usam apenas quantidade BTC disponível; não há venda descoberta."}
        </p>

        <details className="rounded-lg border border-border bg-background p-4">
          <summary className="cursor-pointer text-sm font-semibold leading-5 text-foreground">
            Metadados avançados
          </summary>
          <div className="mt-4 grid gap-3">
            <LabeledInput label="Operador" name="actor_id" defaultValue="dashboard" />
            <LabeledInput label="Motivo" name="reason" defaultValue="Ordem manual Testnet" />
          </div>
        </details>

        <PrimaryButton>
          <Send size={16} aria-hidden="true" />
          Enviar ordem Testnet
        </PrimaryButton>
      </form>
    </Panel>
  );
}

function sideButtonClass(active: boolean) {
  return cx(
    "min-h-10 rounded-md px-3 text-sm font-medium leading-none transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    active ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-background hover:text-foreground",
  );
}
