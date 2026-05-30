# Aurum Frontend Design

## Direcao vigente

O frontend do Aurum deve parecer parte da mesma familia visual do projeto de referencia `workspace-web`, preservando a natureza de dashboard operacional de trading. A referencia visual local e:

`/home/victormmelo/projects/microservices/rvx/workspace/workspace-web`

Essa decisao substitui a direcao Apple anterior para o app operacional. A tela inicial continua sendo dashboard, nao landing page.

## Escopo de produto preservado

- Binance Spot Testnet.
- Par BTCUSDT.
- Estrategia long-only.
- Sem alavancagem.
- Sem execucao operacional em Mainnet dentro do MVP.

## Tokens principais

Os tokens ficam em `apps/web/app/globals.css` usando TailwindCSS v4 `@theme`. O Aurum deve manter aliases legados (`canvas`, `ink`, `hairline`) somente para compatibilidade com telas existentes, mas novos componentes devem preferir os tokens semanticos do workspace-web.

### Cores

| Token | Valor | Uso |
|---|---:|---|
| `--primary` | `#107e59` | Marca RVX, botoes primarios, sidebar, links e estados ativos |
| `--primary-dark` | `#0d3d2d` | Blocos escuros, areas JSON/codigo e apoio de contraste |
| `--brand-lime` | `#63b32e` | Destaques pontuais, nao usar como cor dominante |
| `--dashboard-background` | `color-mix(in srgb, var(--primary) 8%, white)` | Fundo geral do dashboard |
| `--background` | branco | Topbar, inputs, superficies internas |
| `--foreground` | preto | Texto principal |
| `--card` | branco | Cards e paineis |
| `--muted` | cinza claro | Areas secundarias, stat pills, empty states |
| `--muted-foreground` | cinza medio | Labels, descricoes e metadados |
| `--border` / `--input` | cinza claro | Bordas e campos |
| `--success`, `--warning`, `--destructive`, `--info` | OKLCH semantico | Estados operacionais |
| `--sidebar` | `#107e59` | Fundo da navegacao lateral |
| `--sidebar-accent` | mistura de branco com `--primary` | Item ativo/hover da sidebar |

## Tipografia

- Fonte principal: Poppins via `next/font/google`.
- Fonte mono: Geist Mono via `next/font/google`.
- Corpo: `text-sm`/`text-base`, peso 400.
- Labels e metadados: `text-xs` ou `text-sm`, peso 500, `text-muted-foreground`.
- Titulos de pagina: `text-3xl md:text-4xl`, `font-bold`, `tracking-tight`.
- Titulos de card: `text-xl`, `font-semibold`, `tracking-tight`.
- Nao usar letter-spacing negativo como regra geral no Aurum.

## Layout base

O `AppShell` do Aurum deve seguir o padrao operacional do workspace-web:

- Topbar fixa branca, `height: var(--dashboard-topbar-height)`, borda inferior e sombra sutil.
- Sidebar verde fixa/sticky no desktop, abaixo da topbar.
- Fundo do conteudo em `--dashboard-background`.
- Conteudo com largura maxima ampla (`max-w-[1600px]`), padding responsivo e densidade de dashboard.
- Navegacao principal na sidebar, com item ativo em `--sidebar-accent`.
- Em telas pequenas, a navegacao pode virar uma faixa horizontal/grade abaixo da topbar.

## Componentes

### Cards e paineis

- Usar `rounded-xl border border-border bg-card shadow-sm`.
- Padding padrao: `p-5 md:p-6`.
- Nao criar cards dentro de cards, exceto itens repetidos ou estados explicitamente em lista.
- Evitar sombras pesadas, gradientes decorativos e fundos de marketing.

### Botoes

- Primario: `bg-primary text-primary-foreground hover:bg-primary/90`.
- Secundario/outline: `border border-input bg-background hover:bg-accent`.
- Raio: `rounded-md`.
- Altura minima: `h-10` ou `h-12` para formularios.
- Usar icones Lucide quando a acao tiver simbolo claro.

### Badges e status

- Usar `rounded-md`, texto `text-xs font-medium`.
- Estados:
  - Positivo: `border-primary/25 bg-primary/10 text-primary`.
  - Alerta: `border-warning/30 bg-warning/15 text-foreground`.
  - Perigo: `border-destructive/30 bg-destructive/10 text-destructive`.
  - Neutro: `border-border bg-background text-foreground`.

### Inputs, selects e textareas

- `min-h-12 rounded-md border border-input bg-background px-3 py-2 text-sm`.
- Foco com `ring-2 ring-ring ring-offset-2`.
- Placeholders em `text-muted-foreground`.
- Nao criar CSS modules ou classes globais semanticas para campos.

### Tabelas e listas

- Preferir superficies brancas, bordas `border-border`, cabecalhos com `text-muted-foreground`.
- Linhas devem preservar densidade operacional e legibilidade.
- Estados vazios usam borda tracejada e fundo `muted`.

### Codigo e JSON

- Usar `--primary-dark` como fundo escuro.
- Texto em `primary-foreground`.
- `rounded-lg`, padding compacto e fonte mono.

## Tailwind e CSS

- TailwindCSS e o unico sistema de styling do frontend.
- `apps/web/app/globals.css` deve permanecer limitado a:
  - `@import "tailwindcss"`;
  - tokens `@theme`;
  - variaveis CSS globais derivadas deste documento;
  - estilos base minimos.
- Nao criar CSS modules, arquivos CSS de componente ou classes globais semanticas.
- Antes de criar novo padrao visual, procurar componentes em `apps/web/components`.

## Do

- Reutilizar `AppShell`, `Panel`, `PanelHeader`, `MetricCard`, `StatusPill`, `Notice`, `PrimaryButton`, `IconTextButton`, `LabeledInput` e componentes compartilhados.
- Manter a experiencia de dashboard operacional.
- Usar `#107e59` como cor dominante de marca e navegacao.
- Manter Poppins em todo o app.
- Usar raio moderado (`rounded-md`/`rounded-lg`/`rounded-xl`) de acordo com o tipo de componente.
- Usar `rounded-full` apenas para circulos reais, como avatar, ponto de status ou contador circular.

## Don't

- Nao transformar telas em landing page.
- Nao copiar regras de negocio do workspace-web.
- Nao usar gradientes decorativos, hero marketing ou imagens atmosfericas no dashboard.
- Nao usar paleta Apple azul como direcao vigente.
- Nao introduzir outro design system.
- Nao versionar segredos, credenciais Binance, tokens MCP ou chaves operacionais.

## Referencia implementada

Arquivos principais:

- `apps/web/app/globals.css`: tokens RVX Workspace + aliases de compatibilidade.
- `apps/web/app/layout.tsx`: Poppins e Geist Mono.
- `apps/web/components/app-shell.tsx`: topbar/sidebar/layout base.
- `apps/web/components/ui.tsx`: componentes visuais compartilhados.
