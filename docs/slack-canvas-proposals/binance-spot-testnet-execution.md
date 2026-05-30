# Proposta de atualização do Slack Canvas: execução Binance Spot Testnet

Esta proposta deve ser aplicada ao Canvas principal do projeto Aurum quando o
conector Slack estiver autenticado novamente. Ela registra decisões duráveis de
arquitetura, risco, execução e operação Testnet.

## Escopo operacional do MVP

- O MVP permanece restrito a Binance Spot Testnet, `BTCUSDT`, long-only e sem
  alavancagem.
- Mainnet continua fora de escopo e explicitamente bloqueado no adapter
  `binance_mainnet`.
- Credenciais reais de Binance, MCP tokens, chaves de produção e segredos
  operacionais não devem ser versionados.
- `BINANCE_API_KEY` e `BINANCE_API_SECRET` são lidos exclusivamente do ambiente
  local/operacional.

## Arquitetura de execução

- A execução passa por um `OrderService` central.
- Ordem manual e ordem gerada pelo robô usam o mesmo serviço, o mesmo adapter, a
  mesma validação de risco, a mesma auditoria e a mesma persistência.
- Existem adapters separados:
  - `dry_run`: usado para paper mode e testes sem submissão externa.
  - `binance_testnet`: usado para endpoints privados assinados da Binance Spot
    Testnet.
  - `binance_mainnet`: interface futura, bloqueada no MVP.
- O cliente privado assina endpoints Binance com HMAC SHA-256 e suporta
  `/account`, `/order` e `/myTrades`.

## Carteira e fonte da verdade

- Em Testnet, saldo manual não é fonte da verdade.
- O reconciliador de carteira lê `/account` da Binance Spot Testnet e grava
  `portfolio_snapshots`.
- O dashboard/API leem o último snapshot persistido.
- `positions` é atualizado a partir do saldo BTC reconciliado e do preço de
  mercado mais recente.

## Persistência e reconciliação de ordens

- Toda ordem persistida em `orders` deve usar status Binance permitido:
  `NEW`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `REJECTED` ou `EXPIRED`.
- Fills retornados pela Binance são persistidos em `order_fills`.
- Fills podem vir da resposta `FULL` de ordem (`tradeId`) ou de `/myTrades`
  (`id`).
- Falhas de submissão assinada após validação local devem persistir ordem
  `REJECTED` e evento de auditoria `order.rejected`.
- Reconciliação de ordens abertas consulta Binance e atualiza status, preço
  médio, quantidade executada e fills.

## Bloqueios de segurança

Execução Testnet deve ser bloqueada quando houver:

- Robô pausado.
- Emergency stop.
- Ambiente diferente de `testnet`.
- Base URL diferente de Binance Spot Testnet.
- Símbolo diferente de `BTCUSDT`.
- Dados de mercado stale.
- Snapshot de carteira ausente.
- Saldo insuficiente em BTC ou USDT.
- Configuração ativa de risco ausente.
- Limite de risco/exposição excedido.
- Tentativa de Mainnet.

## Operação Testnet

- Configuração mínima:
  - `AURUM_ENVIRONMENT=testnet`
  - `TRADING_SYMBOL=BTCUSDT`
  - `BINANCE_SPOT_BASE_URL=https://testnet.binance.vision/api/v3`
  - `BINANCE_API_KEY` e `BINANCE_API_SECRET` definidos no ambiente local.
- Endpoints operacionais:
  - `POST /portfolio/reconcile`
  - `POST /operations/manual-order`
  - `POST /operations/reconcile`
  - `GET /portfolio/status`
  - `GET /operations/orders`
  - `GET /operations/fills`
- O runbook canônico de validação ponta a ponta é
  `docs/runbooks/testnet-validation-checklist.md`.

## Critério de promoção futura

- Esta decisão não autoriza Mainnet.
- Qualquer Mainnet futura exige nova decisão no Slack Canvas, issue Linear
  dedicada, checklist Mainnet completo, evidência de Testnet e revisão de
  segurança.
