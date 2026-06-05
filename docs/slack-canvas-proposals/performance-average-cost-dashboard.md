# Proposta de atualização do Slack Canvas: performance por custo médio

Esta proposta deve ser aplicada ao Canvas principal do projeto Aurum quando o
conector Slack estiver autenticado. Ela registra a decisão durável de apuração
financeira para o painel operacional.

## Decisão de produto

- A tela `Performance` passa a ser a fonte gerencial para responder se a
  estratégia está ganhando ou perdendo dinheiro.
- A apuração usa custo médio, não FIFO.
- Compras aumentam a posição, o custo total e o custo médio.
- Vendas realizam lucro ou prejuízo proporcional à quantidade vendida.
- Posição aberta continua sendo demonstrada separadamente como PnL não
  realizado.
- O usuário deve conseguir filtrar por `7d`, `30d`, `90d`, mês atual, ano atual
  e desde o início.

## Métricas esperadas

- Lucro realizado no período.
- PnL aberto da posição atual.
- Resultado total, somando realizado e aberto.
- Patrimônio inicial e final do período.
- Retorno percentual do patrimônio.
- Taxas estimadas em USDT.
- Quantidade de vendas realizadas.
- Taxa de acerto.
- Lucro médio, prejuízo médio, maior ganho e maior perda.
- Drawdown estimado pela curva de patrimônio.

## Escopo preservado

- Binance Spot Testnet.
- `BTCUSDT`.
- Long-only.
- Sem alavancagem.
- Sem autorização de Mainnet no MVP.

## Observação operacional

O cálculo inicial pode ser reconstruído dinamicamente a partir de `orders`,
`order_fills` e `portfolio_snapshots`, mantendo o histórico reprocessável. Uma
tabela materializada de performance só deve ser adicionada se houver necessidade
de auditoria imutável ou ganho de performance.
