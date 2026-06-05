import {
  Activity,
  Bot,
  FileDown,
  Gauge,
  KeyRound,
  LineChart,
  ReceiptText,
  Settings2,
  Wallet,
} from "lucide-react";

import type { NavItem } from "@/components/ui";

export const navItems = [
  { label: "Dashboard", href: "/", icon: Gauge },
  { label: "Mercado", href: "/market", icon: LineChart },
  { label: "Carteira", href: "/portfolio", icon: Wallet },
  { label: "Operações", href: "/operations", icon: Activity },
  { label: "Performance", href: "/performance", icon: ReceiptText },
  { label: "Decisões", href: "/decisions", icon: Bot },
  { label: "Estratégias", href: "/configs", icon: Settings2 },
  { label: "MCP", href: "/mcp", icon: KeyRound },
  { label: "Exportações", href: "/exports", icon: FileDown },
] as const satisfies readonly NavItem[];
